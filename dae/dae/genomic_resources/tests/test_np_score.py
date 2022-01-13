from dae.genomic_resources import NPScoreResource
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_the_simplest_np_score():
    res: NPScoreResource = build_a_test_resource({
        "genomic_resource.yaml": '''
            type: np_score
            table:
                filename: data.mem
            scores:
                - id: cadd_raw
                  type: float
                  desc: ""
                  name: s1
        ''',
        "data.mem": '''
            chrom  pos_begin  pos_end  reference  alternative  s1
            1      10         15       A          G            0.02
            1      10         15       A          C            0.03
            1      10         15       A          T            0.04
            1      16         19       C          G            0.03
            1      16         19       C          T            0.04
            1      16         19       C          A            0.05
        '''
    })
    assert res.get_resource_type() == "np_score"
    assert res.open()
    assert res.get_all_scores() == ["cadd_raw"]
    assert res.fetch_scores("1", 11, "A", "C") == {"cadd_raw": 0.03}

    assert res.fetch_scores_agg("1", 10, 11) == {"cadd_raw": 0.04}
    assert res.fetch_scores_agg("1", 15, 16) == {"cadd_raw": 0.045}


def test_np_score_aggregation():
    res: NPScoreResource = build_a_test_resource({
        GR_CONF_FILE_NAME: '''
            type: np_score
            table:
                filename: data.mem
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
        ''',
        "data.mem": '''
            chrom  pos_begin  pos_end  reference  alternative  s1    s2
            1      10         15       A          G            0.02  2
            1      10         15       A          C            0.03  -1
            1      10         15       A          T            0.04  4
            1      16         19       C          G            0.03  3
            1      16         19       C          T            0.04  EMPTY
            1      16         19       C          A            0.05  0
        '''
    })
    assert res.get_resource_type() == "np_score"
    assert res.open()

    assert res.table.chrom_column_i == 0
    assert res.table.pos_begin_column_i == 1
    assert res.table.pos_end_column_i == 2

    assert res.fetch_scores_agg("1", 14, 18, ["cadd_raw"]) == \
        {"cadd_raw": (2*0.04 + 2*0.05) / 4.}

    assert res.fetch_scores_agg(
        "1", 14, 18, ["cadd_raw"],
        non_default_pos_aggregators={"cadd_raw": "max"}) == \
        {"cadd_raw": 0.05}

    assert res.fetch_scores_agg("1", 14, 18, ["cadd_test"]) == \
        {"cadd_test": 3.0}

    assert res.fetch_scores_agg(
        "1", 14, 18, ["cadd_test"],
        non_default_pos_aggregators={"cadd_test": "min"}) == \
        {"cadd_test": 1.5}

    assert res.fetch_scores_agg(
        "1", 14, 18, ["cadd_test"],
        non_default_pos_aggregators={"cadd_test": "min"},
        non_default_nuc_aggregators={"cadd_test": "min"}) == \
        {"cadd_test": 0}
