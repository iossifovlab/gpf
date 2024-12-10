# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.genomic_scores import AlleleScore, AlleleScoreQuery
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_resource


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
