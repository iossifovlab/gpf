# import pytest
# import pandas as pd
# from dae.pheno_browser.graphs import draw_linregres
# from dae.variants.attributes import Role, Sex


# def test_linregres_notcorrelated():
#     df = pd.DataFrame(
#         {
#             "i1.m1": [1, 1, 2, 2, 3, 3],
#             "age": [1, 1, 1, 1, 1, 1],
#             "role": [
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#             ],
#             "sex": [
#                 Sex.male,
#                 Sex.female,
#                 Sex.male,
#                 Sex.female,
#                 Sex.male,
#                 Sex.female,
#             ],
#         }
#     )
#     res_male, res_female = draw_linregres(df, "age", "i1.m1")
#     expected_value = 7.41799e-2
#     assert res_male is not None
#     assert res_female is not None
#     assert res_male.pvalues["age"] == pytest.approx(expected_value)
#     assert res_female.pvalues["age"] == pytest.approx(expected_value)


# def test_linregres_positive():
#     df = pd.DataFrame(
#         {
#             "i1.m1": [1, 1, 2, 2, 3, 3],
#             "age": [1, 1, 2, 2, 3, 3],
#             "role": [
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#             ],
#             "sex": [
#                 Sex.male,
#                 Sex.female,
#                 Sex.male,
#                 Sex.female,
#                 Sex.male,
#                 Sex.female,
#             ],
#         }
#     )
#     res_male, res_female = draw_linregres(df, "age", "i1.m1")
#     expected_value = 1.18e-15
#     assert res_male is not None
#     assert res_female is not None
#     assert res_male.pvalues["age"] == pytest.approx(expected_value)
#     assert res_female.pvalues["age"] == pytest.approx(expected_value)


# def test_linregres_negative():
#     df = pd.DataFrame(
#         {
#             "i1.m1": [1, 1, 2, 2, 3, 3],
#             "age": [3, 3, 2, 2, 1, 1],
#             "role": [
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#                 Role.prb,
#             ],
#             "sex": [
#                 Sex.male,
#                 Sex.female,
#                 Sex.male,
#                 Sex.female,
#                 Sex.male,
#                 Sex.female,
#             ],
#         }
#     )
#     res_male, res_female = draw_linregres(df, "age", "i1.m1")
#     expected_value = 6.92e-16
#     assert res_male is not None
#     assert res_female is not None
#     assert res_male.pvalues["age"] == pytest.approx(expected_value)
#     assert res_female.pvalues["age"] == pytest.approx(expected_value)
