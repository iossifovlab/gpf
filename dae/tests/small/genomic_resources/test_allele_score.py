# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest
from dae.genomic_resources.aggregators import (
    MaxAggregator,
    MeanAggregator,
    MinAggregator,
)
from dae.genomic_resources.genomic_scores import AlleleScore, AlleleScoreQuery
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, GenomicResource
from dae.genomic_resources.testing import build_inmemory_test_resource


def build_allele_resource(config: str, data: str) -> GenomicResource:
    return build_inmemory_test_resource({
        GR_CONF_FILE_NAME: textwrap.dedent(config),
        "data.mem": textwrap.dedent(data),
    })


def test_the_simplest_allele_score() -> None:
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
            1      10         A          C            0.03
            1      10         A          A            0.04
            1      16         CA         G            0.03
            1      16         C          T            0.04
            1      16         C          A            0.05
        """,
    })
    assert res.get_type() == "allele_score"

    score = AlleleScore(res)
    score.open()

    assert score.get_all_scores() == ["freq"]
    assert score.fetch_scores("1", 10, "A", "C") == [0.03]


def test_allele_score_fetch_region() -> None:
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
            1      10         A          C            0.03
            1      10         A          A            0.04
            1      16         CA         G            0.03
            1      16         C          T            0.04
            1      16         C          A            0.05
            2      16         CA         G            0.03
            2      16         C          T            EMPTY
            2      16         C          A            0.05
        """,
    })
    score = AlleleScore(res)
    score.open()

    # The in-mem table will sort the records. In this example it will sort
    # the alternatives column (previous columns are the same). That is why
    # the scores (freq) appear out of order
    assert list(score._fetch_region_values("1", 10, 11, ["freq"])) == \
        [(10, 10, [0.04]),
         (10, 10, [0.03]),
         (10, 10, [0.02])]

    assert list(score._fetch_region_values("1", 10, 16, ["freq"])) == \
        [(10, 10, [0.04]),
         (10, 10, [0.03]),
         (10, 10, [0.02]),
         (16, 16, [0.05]),
         (16, 16, [0.04]),
         (16, 16, [0.03])]

    assert list(score._fetch_region_values("2", None, None, ["freq"])) == [
        (16, 16, [0.05]),
        (16, 16, [None]),
        (16, 16, [0.03]),
    ]


def test_allele_score_missing_alt() -> None:
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
            1      10         A          .            0.03
        """,
    })
    score = AlleleScore(res)
    score.open()
    assert score.fetch_scores("1", 10, "A", "A", ["freq"]) is None
    assert score.fetch_scores("1", 10, "A", "G", ["freq"]) is None
    assert score.fetch_scores("1", 10, "A", "T", ["freq"]) is None
    assert score.fetch_scores("1", 10, "A", "C", ["freq"]) is None


@pytest.mark.parametrize("region,pos_aggregator,allele_aggregator,expected", [
    (("1", 10, 13), "max", "max", 0.4),
    (("1", 10, 13), "min", "min", 0.2),
    (("1", 10, 16), "min", "min", 0.03),
    (("1", 10, 16), None, None, (0.4 + 0.05) / 2.0),
])
def test_allele_score_fetch_agg(
        region: tuple[str, int, int],
        pos_aggregator: str | None, allele_aggregator: str | None,
        expected: float) -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            allele_score_mode: alleles
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
            1      10         A          C            0.2
            1      10         A          G            0.3
            1      10         A          T            0.4
            1      16         C          A            0.03
            1      16         C          AG           0.04
            1      16         C          G            0.05
            2      16         C          GA           0.06
            2      16         C          T            0.07
            2      16         C          TA           0.08
        """,
    })
    score = AlleleScore(res)
    score.open()

    result = score.fetch_scores_agg(
        *region,
        [AlleleScoreQuery("freq", pos_aggregator, allele_aggregator)])
    assert result is not None
    assert len(result) == 1
    assert result[0].get_final() == expected


def test_allele_score_mode_defaults_to_alleles() -> None:
    res = build_allele_resource(
        """
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
        """
        chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        """,
    )

    score = AlleleScore(res)

    assert score.alleles_mode()
    assert not score.substitutions_mode()


def test_allele_score_mode_substitutions_config() -> None:
    res = build_allele_resource(
        """
        type: allele_score
        allele_score_mode: substitutions
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
        """
        chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        """,
    )

    score = AlleleScore(res)

    assert score.substitutions_mode()
    assert not score.alleles_mode()


def test_allele_score_np_score_defaults_to_substitutions(
        caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("WARNING")
    res = build_allele_resource(
        """
        type: np_score
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
        """
        chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        """,
    )

    score = AlleleScore(res)

    assert score.substitutions_mode()
    assert not score.alleles_mode()
    assert any("deprecated" in rec.message for rec in caplog.records)


def test_allele_score_fetch_scores_invalid_chromosome() -> None:
    res = build_allele_resource(
        """
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
        """
        chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        """,
    )

    score = AlleleScore(res)
    score.open()

    with pytest.raises(
        ValueError, match="not among the available chromosomes",
    ):
        score.fetch_scores("2", 10, "A", "G")


def test_allele_score_fetch_region_rejects_spanning_records() -> None:
    res = build_allele_resource(
        """
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
        """
        chrom  pos_begin  pos_end  reference  alternative  freq
        1      10         12       A          G            0.02
        """,
    )

    score = AlleleScore(res)
    score.open()

    with pytest.raises(ValueError, match="value for a region in allele score"):
        list(score.fetch_region("1", 10, 12, ["freq"]))


def test_allele_score_build_scores_agg_defaults() -> None:
    res = build_allele_resource(
        """
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
        """
        chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        """,
    )

    score = AlleleScore(res)

    aggs = score._build_scores_agg([AlleleScoreQuery("freq")])
    assert len(aggs) == 1
    assert isinstance(aggs[0].position_aggregator, MeanAggregator)
    assert isinstance(aggs[0].allele_aggregator, MaxAggregator)


def test_allele_score_build_scores_agg_overrides() -> None:
    res = build_allele_resource(
        """
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
        """
        chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        """,
    )

    score = AlleleScore(res)

    aggs = score._build_scores_agg([
        AlleleScoreQuery("freq", position_aggregator="min",
                         allele_aggregator="mean"),
    ])
    assert len(aggs) == 1
    assert isinstance(aggs[0].position_aggregator, MinAggregator)
    assert isinstance(aggs[0].allele_aggregator, MeanAggregator)
