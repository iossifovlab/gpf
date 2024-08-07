# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.genomic_scores import NPScore, NPScoreQuery
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_resource
from dae.testing import convert_to_tab_separated


def test_the_simplest_np_score() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: np_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: cadd_raw
                  name: s1
                  type: float
                  desc: ""
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  reference  alternative  s1
            1      10         15       A          G            0.02
            1      10         15       A          C            0.03
            1      10         15       A          T            0.04
            1      16         19       C          G            0.03
            1      16         19       C          T            0.04
            1      16         19       C          A            0.05
        """,
    })
    assert res.get_type() == "np_score"
    score = NPScore(res)
    score.open()

    assert score.get_all_scores() == ["cadd_raw"]
    assert score.fetch_scores("1", 11, "A", "C") == [0.03]

    assert score.fetch_scores_agg("1", 10, 11) == [0.04]
    assert score.fetch_scores_agg("1", 15, 16) == [0.045]


def test_np_score_aggregation() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: np_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: cadd_raw
                  type: float
                  desc: ""
                  name: s1

                - id: cadd_test
                  type: int
                  position_aggregator: max
                  nucleotide_aggregator: mean
                  na_values: "-1"
                  desc: ""
                  name: s2
        """,
        "data.mem": convert_to_tab_separated("""
            chrom  pos_begin  pos_end  reference  alternative  s1    s2
            1      10         15       A          G            0.02  2
            1      10         15       A          C            0.03  -1
            1      10         15       A          T            0.04  4
            1      16         19       C          G            0.03  3
            1      16         19       C          T            0.04  EMPTY
            1      16         19       C          A            0.05  0
        """),
    })

    assert res.get_type() == "np_score"
    score = NPScore(res)
    score.open()

    assert score.table.chrom_key == 0  # "chrom"
    assert score.table.pos_begin_key == 1  # "pos_begin"
    assert score.table.pos_end_key == 2  # "pos_end"

    assert score.fetch_scores_agg(
        "1", 14, 18, [NPScoreQuery("cadd_raw")]) == \
        [(2 * 0.04 + 2 * 0.05) / 4.]

    assert score.fetch_scores_agg(
        "1", 14, 18, [NPScoreQuery("cadd_raw", "max")]) == \
        [0.05]

    assert score.fetch_scores_agg(
        "1", 14, 18, [NPScoreQuery("cadd_test")]) == \
        [3.0]

    assert score.fetch_scores_agg(
        "1", 14, 18, [NPScoreQuery("cadd_test", "min")]) == \
        [1.5]

    assert score.fetch_scores_agg(
        "1", 14, 18, [NPScoreQuery("cadd_test", "min", "min")]) == \
        [0]


def test_np_score_fetch_region() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: np_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
                - id: cadd_raw
                  type: float
                  desc: ""
                  name: s1

                - id: cadd_test
                  type: int
                  position_aggregator: max
                  nucleotide_aggregator: mean
                  na_values: "-1"
                  desc: ""
                  name: s2
        """,
        "data.mem": convert_to_tab_separated("""
            chrom  pos_begin  pos_end  reference  alternative  s1    s2
            1      10         15       A          G            0.02  2
            1      10         15       A          C            0.03  -1
            1      10         15       A          T            0.04  4
            1      16         19       C          G            0.03  3
            1      16         19       C          T            0.04  EMPTY
            1      16         19       C          A            0.05  0
            2      16         19       C          A            0.03  3
            2      16         19       C          T            0.04  3
            2      16         19       C          G            0.05  4
        """),
    })
    score = NPScore(res).open()

    # The in-mem table will sort the records. In this example it will sort
    # the alternatives column (previous columns are the same). That is why
    # the scores (freq) appear out of order
    assert list(score.fetch_region("1", 14, 16, ["cadd_raw"])) == \
        [{"cadd_raw": 0.03},
         {"cadd_raw": 0.03},
         {"cadd_raw": 0.02},
         {"cadd_raw": 0.02},
         {"cadd_raw": 0.04},
         {"cadd_raw": 0.04},
         {"cadd_raw": 0.05},
         {"cadd_raw": 0.03},
         {"cadd_raw": 0.04}]

    assert list(score.fetch_region("1", 14, 16, ["cadd_test"])) == \
        [{"cadd_test": None},
         {"cadd_test": None},
         {"cadd_test": 2},
         {"cadd_test": 2},
         {"cadd_test": 4},
         {"cadd_test": 4},
         {"cadd_test": 0},
         {"cadd_test": 3},
         {"cadd_test": None}]

    assert list(score.fetch_region("2", 13, 17, ["cadd_test"])) == \
        [{"cadd_test": 3},
         {"cadd_test": 3},
         {"cadd_test": 4},
         {"cadd_test": 4},
         {"cadd_test": 3},
         {"cadd_test": 3}]
