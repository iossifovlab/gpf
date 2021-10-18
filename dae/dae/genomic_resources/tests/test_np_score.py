from dae.genomic_resources import NPScoreResource
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_the_simplest_np_score():
    res: NPScoreResource = build_a_test_resource({
        GR_CONF_FILE_NAME: '''
            type: NPScore
            table:
                filename: data.mem
            scores:
                - id: cadd_raw
                  type: float
                  desc: ""
                  name: s1
        ''',
        "data.mem": '''
            chrom   pos_begin  pos_end   reference    alternative     s1
            1       10         15        A            G               0.02
            1       10         15        A            C               0.03
            1       10         15        A            T               0.04
            1       16         19        C            G               0.03
            1       16         19        C            T               0.04
            1       16         19        C            A               0.05
            2       5          80        T            A               0.01
            2       5          80        T            C               0.02
            2       5          80        T            G               0.03
        '''
    })
    assert res.get_resource_type() == "NPScore"
    assert res.open()
    assert res.get_all_scores() == ["cadd_raw"]
    assert res.fetch_scores("1", 11, "A", "C") == {"cadd_raw": 0.03}

    assert res.fetch_scores_agg("1", 10, 11) == {"cadd_raw": 0.04}
    assert res.fetch_scores_agg("1", 15, 16) == {"cadd_raw": 0.045}

    # assert res.fetch_scores_agg(
    #     "1", 10, 11, non_default_aggregators={"phastCons100way": "max"}) == \
    #     {"phastCons100way": 0.03}


# def test_region_score():
#     res: PositionScoreResource = build_a_test_resource({
#         GR_CONF_FILE_NAME: '''
#             type: PositionScores
#             table:
#                 filename: data.mem
#             scores:
#               - id: phastCons100way
#                 type: float
#                 desc: "The phastCons computed over the tree of 100 \
#                        verterbarte species"
#                 name: s1
#               - id: phastCons5way
#                 type: int
#                 position_aggregator: max
#                 na_values: "-1"
#                 desc: "The phastCons computed over the tree of 5 \
#                        verterbarte species"
#                 name: s2''',
#         "data.mem": '''
#             chrom   pos_begin  pos_end   s1     s2
#             1       10         15        0.02   -1
#             1       17         19        0.03   0
#             1       22         25        0.46   EMPTY
#             2       5          80        0.01   3
#             '''
#     })
#     assert res
#     assert res.open()
#     assert res.table.chrom_column_i == 0
#     assert res.table.pos_begin_column_i == 1
#     assert res.table.pos_end_column_i == 2

#     assert res.fetch_scores("1", 12) == {
#         "phastCons100way": 0.02, "phastCons5way": None}

#     assert res.fetch_scores_agg("1", 13, 18, ["phastCons100way"]) == \
#         {"phastCons100way": (3*0.02 + 2*0.03) / 5.}
#     assert res.fetch_scores_agg(
#         "1", 13, 18, ["phastCons100way"],
#         non_default_aggregators={"phastCons100way": "max"}) == \
#         {"phastCons100way": 0.03}

#     assert res.fetch_scores_agg("1", 13, 18, ["phastCons5way"]) == \
#         {"phastCons5way": 0}
#     assert res.fetch_scores_agg(
#         "1", 13, 18, ["phastCons5way"],
#         non_default_aggregators={"phastCons5way": "mean"}) == \
#         {"phastCons5way": 0/2}
