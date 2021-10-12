from dae.genomic_resources import PositionScoreResource
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_the_simplest_position_score():
    res: PositionScoreResource = build_a_test_resource({
        GR_CONF_FILE_NAME: '''
            type: PositionScores
            table:
                file: data.mem
            scores:
              - id: phastCons100way
                type: float
                desc: "The phastCons computed over the tree of 100 \
                       verterbarte species"
                name: s1''',
        "data.mem": '''
            chrom   pos_begin  s1
            1       10         0.02
            1       11         0.03
            1       15         0.46
            2       8          0.01
            '''
    })
    assert res.get_resource_type() == "PositionScores"
    assert res.open()
    assert res.get_all_scores() == ["phastCons100way"]
    assert res.fetch_scores("1", 11) == {"phastCons100way": 0.03}
    assert res.fetch_scores("1", 15) == {"phastCons100way": 0.46}
    assert res.fetch_scores("2", 8) == {"phastCons100way": 0.01}
    assert res.fetch_scores("1", 10) == {"phastCons100way": 0.02}
    assert res.fetch_scores("1", 12) is None

    assert res.fetch_scores_agg("1", 10, 11) == {"phastCons100way": 0.025}
    assert res.fetch_scores_agg(
        "1", 10, 11, non_default_aggregators={"phastCons100way": "max"}) == \
        {"phastCons100way": 0.03}


def test_region_score():
    res: PositionScoreResource = build_a_test_resource({
        GR_CONF_FILE_NAME: '''
            type: PositionScores
            table:
                file: data.mem
            scores:
              - id: phastCons100way
                type: float
                desc: "The phastCons computed over the tree of 100 \
                       verterbarte species"
                name: s1
              - id: phastCons5way
                type: int
                position_aggregator: max
                na_values: "-1"
                desc: "The phastCons computed over the tree of 5 \
                       verterbarte species"
                name: s2''',
        "data.mem": '''
            chrom   pos_begin  pos_end   s1     s2
            1       10   15    0.02   -1
            1       17   19    0.03   0
            1       22   25    0.46   EMPTY
            2       5    80    0.01   3
            '''
    })
    assert res
    assert res.open()
    assert res.infile.chr_column_i == 0
    assert res.infile.pos_begin_column_i == 1
    assert res.infile.pos_end_column_i == 2

    assert res.fetch_scores("1", 12) == {
        "phastCons100way": 0.02, "phastCons5way": -1.}
    assert res.fetch_scores_agg("1", 13, 18, ["phastCons100way"]) == \
        {"phastCons100way": (3*0.02 + 2*0.03) / 5.}
    assert res.fetch_scores_agg(
        "1", 13, 18, ["phastCons100way"],
        non_default_aggregators={"phastCons100way": "max"}) == \
        {"phastCons100way": 0.03}

    assert res.fetch_scores_agg("1", 13, 18, ["phastCons5way"]) == \
        {"phastCons5way": 0}
    assert res.fetch_scores_agg(
        "1", 13, 18, ["phastCons5way"],
        non_default_aggregators={"phastCons5way": "mean"}) == \
        {"phastCons5way": 0/2}
