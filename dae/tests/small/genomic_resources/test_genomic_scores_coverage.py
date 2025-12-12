# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Tests to improve coverage of genomic_scores module."""
import logging

import pytest
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.genomic_position_table.line import Line
from dae.genomic_resources.genomic_scores import (
    AlleleScore,
    AlleleScoreQuery,
    CnvCollection,
    PositionScore,
    PositionScoreQuery,
    ScoreLine,
    _ScoreDef,
    build_score_from_resource,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_resource


def test_score_def_to_public() -> None:
    """Test _ScoreDef.to_public() method."""
    score_def = _ScoreDef(
        score_id="test_score",
        desc="Test description",
        value_type="float",
        pos_aggregator="mean",
        allele_aggregator="max",
        small_values_desc="Less is better",
        large_values_desc="More is better",
        col_name="score_col",
        col_index=None,
        hist_conf=None,
        value_parser=None,
        na_values=None,
    )
    public_def = score_def.to_public()
    assert public_def.score_id == "test_score"
    assert public_def.desc == "Test description"


def test_score_line_get_score_value_parser_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test ScoreLine.get_score() when value parser raises exception."""

    def bad_parser(value: str) -> float:  # noqa
        raise ValueError("Parse error")

    raw_line = ("chr1", 1, 10, "invalid")
    score_defs = {
        "test_score": _ScoreDef(
            score_id="test_score",
            desc="",
            value_type="float",
            pos_aggregator=None,
            allele_aggregator=None,
            small_values_desc=None,
            large_values_desc=None,
            col_name="score",
            col_index=None,
            hist_conf=None,
            value_parser=bad_parser,
            na_values=None,
            score_index=3,
        ),
    }
    line = ScoreLine(Line(raw_line), score_defs)

    result = line.get_score("test_score")
    assert result is None
    assert any(
        "unable to parse value" in rec.message
        for rec in caplog.records)


def test_deprecated_nucleotide_aggregator(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test deprecated nucleotide_aggregator configuration."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
                  nucleotide_aggregator: max
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
        """,
    })
    score = AlleleScore(res)
    score.open()
    assert any("deprecated" in rec.message for rec in caplog.records)


def test_default_annotation_attribute() -> None:
    """Test get_default_annotation_attribute with custom names."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score1
                  type: float
                  name: score1
                - id: score2
                  type: float
                  name: score2
            default_annotation:
                - source: score1
                  name: custom_name
                - source: score2
        """,
        "data.mem": """
            chrom  pos_begin  score1  score2
            1      10         0.1     0.2
        """,
    })

    score = build_score_from_resource(res)
    score.open()

    attr = score.get_default_annotation_attribute("score1")
    assert attr == "custom_name"

    attr2 = score.get_default_annotation_attribute("score2")
    assert attr2 == "score2"


def test_genomic_score_is_open() -> None:
    """Test is_open() method."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    score = build_score_from_resource(res)
    assert not score.is_open()
    score.open()
    assert score.is_open()
    score.close()
    assert not score.is_open()


def test_genomic_score_open_already_opened(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test opening an already opened genomic score."""
    caplog.set_level(logging.INFO)

    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    score = build_score_from_resource(res)
    score.open()
    score.open()  # Open again
    assert any(
        "opening already opened" in rec.message for rec in caplog.records
    )


def test_genomic_score_context_manager_with_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test context manager exit with exception."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    score = build_score_from_resource(res)
    try:
        with score.open():
            raise RuntimeError("Test exception")  # noqa
    except RuntimeError:
        pass

    assert any(
        "exception while working" in rec.message
        for rec in caplog.records)


def test_position_score_multiple_values_for_position() -> None:
    """Test error when multiple values exist for same position."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  score
            1      10         15       0.1
            1      12         18       0.2
        """,
    })

    score = PositionScore(res)
    score.open()

    with pytest.raises(ValueError, match="multiple values"):
        list(score._fetch_region_values("1", 10, 20, ["score"]))


def test_position_score_fetch_scores_multiple_lines() -> None:
    """Test error when fetch_scores returns multiple lines."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  score
            1      10         10       0.1
            1      10         10       0.2
        """,
    })

    score = PositionScore(res)
    score.open()

    with pytest.raises(ValueError, match="multiple values"):
        score.fetch_scores("1", 10)


def test_position_score_fetch_scores_agg_invalid_chromosome() -> None:
    """Test fetch_scores_agg with invalid chromosome."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
                  position_aggregator: mean
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    score = PositionScore(res)
    score.open()

    with pytest.raises(ValueError, match="not among the available"):
        score.fetch_scores_agg("chr99", 10, 20)


def test_position_score_build_scores_agg_with_query() -> None:
    """Test _build_scores_agg with PositionScoreQuery objects."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score1
                  type: float
                  name: score1
                  position_aggregator: mean
                - id: score2
                  type: float
                  name: score2
                  position_aggregator: max
        """,
        "data.mem": """
            chrom  pos_begin  score1  score2
            1      10         0.1     0.5
            1      11         0.2     0.6
        """,
    })

    score = PositionScore(res)
    score.open()

    result = score.fetch_scores_agg(
        "1",
        10,
        11,
        [PositionScoreQuery("score1", "max"), PositionScoreQuery("score2")],
    )
    assert len(result) == 2
    assert result[0].get_final() == 0.2
    assert result[1].get_final() == 0.6


def test_allele_score_invalid_resource_type() -> None:
    """Test AlleleScore with invalid resource type."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    with pytest.raises(ValueError, match="should be of"):
        AlleleScore(res)


def test_allele_score_mode_from_name_invalid() -> None:
    """Test AlleleScore.Mode.from_name with invalid name."""
    with pytest.raises(ValueError, match="unknown allele mode"):
        AlleleScore.Mode.from_name("invalid_mode")


def test_allele_score_fetch_region_spanning_record() -> None:
    """Test fetch_region with spanning records (pos_begin != pos_end)."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  reference  alternative  freq
            1      10         15       A          G            0.02
        """,
    })
    score = AlleleScore(res)
    score.open()

    with pytest.raises(ValueError, match="value for a region in allele score"):
        list(score.fetch_region("1", 10, 20, ["freq"]))


def test_allele_score_fetch_region_overlapping_positions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test fetch_region with overlapping positions (same pos, same alleles)."""
    caplog.set_level(logging.DEBUG)

    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
            1      10         A          G            0.03
        """,
    })
    score = AlleleScore(res)
    score.open()

    result = list(score.fetch_region("1", 10, 11, ["freq"]))
    assert len(result) == 2


def test_allele_score_fetch_scores_agg_with_queries() -> None:
    """Test fetch_scores_agg with AlleleScoreQuery objects."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
                  position_aggregator: mean
                  allele_aggregator: max
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
            1      10         A          C            0.04
            1      11         A          T            0.06
        """,
    })

    score = AlleleScore(res)
    score.open()

    result = score.fetch_scores_agg(
        "1",
        10,
        11,
        [AlleleScoreQuery("freq", "max", "min")],
    )
    assert len(result) == 1


def test_allele_score_fetch_scores_agg_empty_lines() -> None:
    """Test fetch_scores_agg with no lines in region."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
                  position_aggregator: mean
                  allele_aggregator: max
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
        """,
    })

    score = AlleleScore(res)
    score.open()

    result = score.fetch_scores_agg("1", 100, 200)
    assert len(result) == 1


def test_cnv_collection_invalid_resource_type() -> None:
    """Test CnvCollection with invalid resource type."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    with pytest.raises(ValueError, match="should be of"):
        CnvCollection(res)


def test_cnv_collection_fetch_cnvs() -> None:
    """Test CnvCollection.fetch_cnvs method."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: cnv_collection
            table:
                filename: data.mem
            scores:
                - id: cnv_type
                  type: str
                  name: cnv_type
                - id: frequency
                  type: float
                  name: frequency
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  cnv_type  frequency
            1      100        200      DEL       0.01
            1      300        400      DUP       0.02
            2      500        600      DEL       0.03
        """,
    })

    cnv_collection = CnvCollection(res)
    cnv_collection.open()

    cnvs = cnv_collection.fetch_cnvs("1", 150, 350)
    assert len(cnvs) == 2
    assert cnvs[0].chrom == "1"
    assert cnvs[0].pos_begin == 100
    assert cnvs[0].pos_end == 200
    assert cnvs[0].attributes["cnv_type"] == "DEL"
    assert cnvs[0].attributes["frequency"] == 0.01

    cnvs = cnv_collection.fetch_cnvs("1", 1000, 2000)
    assert len(cnvs) == 0

    cnvs = cnv_collection.fetch_cnvs("chr99", 1, 100)
    assert len(cnvs) == 0


def test_cnv_collection_not_open() -> None:
    """Test CnvCollection.fetch_cnvs when not opened."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: cnv_collection
            table:
                filename: data.mem
            scores:
                - id: cnv_type
                  type: str
                  name: cnv_type
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  cnv_type
            1      100        200      DEL
        """,
    })

    cnv_collection = CnvCollection(res)

    with pytest.raises(ValueError, match="is not open"):
        cnv_collection.fetch_cnvs("1", 100, 200)


def test_build_score_from_resource_invalid_type() -> None:
    """Test build_score_from_resource with unsupported resource type."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: gene_models
        """,
    })

    with pytest.raises(ValueError, match="is not of score type"):
        build_score_from_resource(res)


def test_validate_scoredefs_column_name_not_in_header() -> None:
    """Test scoredef validation when column_name is not in header."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
                header:
                    - chrom
                    - pos_begin
                    - score1
            scores:
                - id: score
                  type: float
                  column_name: nonexistent_column
        """,
        "data.mem": """
            1  10  0.1
        """,
    })

    score = PositionScore(res)
    with pytest.raises(AssertionError):
        score.open()


def test_validate_scoredefs_column_index_out_of_bounds() -> None:
    """Test scoredef validation when column_index is out of bounds."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
                header:
                    - chrom
                    - pos_begin
                    - score1
            scores:
                - id: score
                  type: float
                  column_index: 10
        """,
        "data.mem": """
            1  10  0.1
        """,
    })

    score = PositionScore(res)
    with pytest.raises(AssertionError):
        score.open()


def test_validate_scoredefs_no_column_name_or_index() -> None:
    """Test scoredef validation when neither column_name nor column_index."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
        """,
        "data.mem": """
            chrom  pos_begin  score
            1      10         0.1
        """,
    })

    score = PositionScore(res)
    with pytest.raises(AssertionError, match="Either an index or name"):
        score.open()


def test_position_score_get_region_scores() -> None:
    """Test PositionScore.get_region_scores method."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  score
            1      10         12       0.1
            1      15         16       0.2
        """,
    })

    score = PositionScore(res)
    score.open()

    result = score.get_region_scores("1", 10, 16, "score")
    assert len(result) == 7
    assert result[0] == 0.1
    assert result[1] == 0.1
    assert result[2] == 0.1
    assert result[3] is None
    assert result[4] is None
    assert result[5] == 0.2
    assert result[6] == 0.2


def test_deprecated_name_and_index_config(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test deprecated 'name' and 'index' configuration options."""
    caplog.set_level(logging.DEBUG)

    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score1
                  type: float
                  name: score1
                - id: score2
                  type: float
                  index: 3
        """,
        "data.mem": """
            chrom  pos_begin  score1  score2
            1      10         0.1     0.2
        """,
    })

    score = PositionScore(res)
    score.open()

    assert any("outdated" in rec.message for rec in caplog.records)


def test_allele_score_invalid_mode_config() -> None:
    """Test AlleleScore with invalid mode configuration."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            allele_score_mode: unknown_mode
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
        """,
    })

    with pytest.raises(ValueError, match="Invalid configuration"):
        AlleleScore(res)


def test_build_score_from_resource_cnv_collection() -> None:
    """Test build_score_from_resource with cnv_collection type."""
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: cnv_collection
            table:
                filename: data.mem
            scores:
                - id: cnv_type
                  type: str
                  name: cnv_type
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  cnv_type
            1      100        200      DEL
        """,
    })

    score = build_score_from_resource(res)
    assert isinstance(score, CnvCollection)


def test_cnv_collection_get_schema() -> None:
    """Test CnvCollection.get_schema() method."""
    schema = CnvCollection.get_schema()
    assert "scores" in schema
    assert "allele_aggregator" in schema["scores"]["schema"]["schema"]
