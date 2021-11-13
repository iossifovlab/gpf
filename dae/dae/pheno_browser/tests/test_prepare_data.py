# import pytest

# import pandas as pd

# from dae.pheno_browser.prepare_data import PreparePhenoBrowserBase

# from dae.variants.attributes import Role, Sex
# from dae.configuration.gpf_config_parser import GPFConfigParser
# from dae.configuration.schemas.phenotype_data import pheno_conf_schema


# def test_augment_measure(fake_phenotype_data, output_dir):
#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     df = prep._augment_measure_values_df(
#         regressor, "test regression", regressand
#     )
#     roles = list(df["role"].unique())
#     assert len(roles) == 3
#     for role in [Role.parent, Role.sib, Role.prb]:
#         assert role in roles
#     assert list(df) == [
#         "person_id",
#         "family_id",
#         "role",
#         "sex",
#         "status",
#         "test regression",
#         "i1.m1",
#     ]
#     assert len(df) > 0


# def test_augment_measure_regressor_no_instrument_name(
#     fake_phenotype_data, output_dir
# ):
#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     exp_df = prep._augment_measure_values_df(
#         regressor, "test regression", regressand
#     )
#     regressor.instrument_name = None
#     df = prep._augment_measure_values_df(
#         regressor, "test regression", regressand
#     )
#     assert list(df) == [
#         "person_id",
#         "family_id",
#         "role",
#         "sex",
#         "status",
#         "test regression",
#         "i1.m1",
#     ]
#     assert len(df) > 0
#     assert list(df["test regression"]) == list(exp_df["test regression"])


# def test_augment_measure_with_identical_measures(
#     fake_phenotype_data, output_dir
# ):
#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.age")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     df = prep._augment_measure_values_df(
#         regressor, "test regression", regressand
#     )
#     assert df is None


# def test_augment_measure_with_nonexistent_regressor(
#     fake_phenotype_data, output_dir
# ):
#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i2.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     regressor.instrument_name = None
#     df = prep._augment_measure_values_df(
#         regressor, "test regression", regressand
#     )
#     assert df is None


# def test_build_regression(mocker, fake_phenotype_data, output_dir):

#     fake_df = pd.DataFrame(
#         {
#             # Only two unique values, in order to test
#             # the MIN_UNIQUE_VALUES check
#             "i1.m1": [1, 2, 1, 2, 1, 2],
#             "age": [1, 2, 3, 4, 5, 6],
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

#     def fake_augment_df(*args):
#         return fake_df

#     def fake_linregres(*args):
#         class Result:
#             pvalues = {"age": 0.123456}

#         res_male = Result()
#         res_female = Result()
#         res_female.pvalues["age"] = 0.654321
#         return (res_male, res_female)

#     def fake_savefig(*args):
#         return ("figsmall", "fig")

#     mocked_linregres = mocker.patch(
#         "dae.pheno_browser.prepare_data.draw_linregres",
#         side_effect=fake_linregres,
#     )
#     mocker.patch(
#         "dae.pheno_browser.prepare_data.PreparePhenoBrowserBase.save_fig",
#         side_effect=fake_savefig,
#     )
#     mocker.patch(
#         "dae.pheno_browser.prepare_data."
#         "PreparePhenoBrowserBase._augment_measure_values_df",
#         side_effect=fake_augment_df,
#     )

#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     jitter = 0.32403423849

#     res = prep.build_regression(regressand, regressor, jitter)
#     assert res is not None
#     assert type(res) is dict

#     mocked_linregres.assert_called_once()
#     df, col1, col2, jitter = mocked_linregres.call_args[0]
#     assert col1 == "age"
#     assert col2 == "i1.m1"
#     assert jitter == 0.32403423849


# def test_build_regression_min_vals(mocker, fake_phenotype_data, output_dir):
#     fake_df = pd.DataFrame(
#         {
#             "i1.m1": [1, 2, 3, 4, 5],
#             "age": [1, 2, 3, 4, 5],
#             "role": [Role.prb, Role.prb, Role.prb, Role.prb, Role.prb],
#             "sex": [Sex.male, Sex.female, Sex.male, Sex.female, Sex.male],
#         }
#     )

#     def fake_augment_df(*args):
#         return fake_df

#     mocker.patch(
#         "dae.pheno_browser.prepare_data."
#         "PreparePhenoBrowserBase._augment_measure_values_df",
#         side_effect=fake_augment_df,
#     )

#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     jitter = 0.32403423849

#     assert prep.build_regression(regressand, regressor, jitter) == {}


# def test_build_regression_min_unique_vals(
#     mocker, fake_phenotype_data, output_dir
# ):
#     fake_df = pd.DataFrame(
#         {
#             "i1.m1": [1, 1, 1, 1, 1, 1],
#             "age": [1, 2, 3, 4, 5, 6],
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

#     def fake_augment_df(*args):
#         return fake_df

#     mocker.patch(
#         "dae.pheno_browser.prepare_data."
#         "PreparePhenoBrowserBase._augment_measure_values_df",
#         side_effect=fake_augment_df,
#     )

#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     jitter = 0.32403423849

#     assert prep.build_regression(regressand, regressor, jitter) == {}


# def test_build_regression_identical_measures(
#     mocker, fake_phenotype_data, output_dir
# ):
#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.age")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     jitter = 0.32403423849

#     assert prep.build_regression(regressand, regressor, jitter) == {}


# def test_build_regression_aug_df_is_none(
#     mocker, fake_phenotype_data, output_dir
# ):
#     def fake_augment_df(*args):
#         return None

#     mocker.patch(
#         "dae.pheno_browser.prepare_data."
#         "PreparePhenoBrowserBase._augment_measure_values_df",
#         side_effect=fake_augment_df,
#     )

#     prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
#     regressand = fake_phenotype_data.get_measure("i1.m1")
#     regressor = fake_phenotype_data.get_measure("i1.age")
#     jitter = 0.32403423849

#     assert prep.build_regression(regressand, regressor, jitter) == {}


# def test_handle_regressions(
#     mocker, fake_phenotype_data, output_dir, fake_phenotype_data_desc_conf
# ):
#     def fake_build_regression(dependent_measure, independent_measure, jitter):
#         return {
#             "regressand": dependent_measure,
#             "regressor": independent_measure,
#             "jitter": jitter,
#             "pvalue_regression_male": 0,
#             "pvalue_regression_female": 0,
#         }

#     mocked = mocker.patch(
#         "dae.pheno_browser.prepare_data."
#         "PreparePhenoBrowserBase.build_regression",
#         side_effect=fake_build_regression,
#     )

#     reg = GPFConfigParser.load_config(
#         fake_phenotype_data_desc_conf, pheno_conf_schema
#     )
#     prep = PreparePhenoBrowserBase(
#         "fake", fake_phenotype_data, output_dir, reg
#     )
#     regressand = fake_phenotype_data.get_measure("i1.m1")

#     res = [r for r in prep.handle_regressions(regressand) if r is not None]
#     assert len(res) == 2
#     assert sorted([r["regression_id"] for r in res]) == sorted(["age", "nviq"])

#     mocked.assert_called()
#     measure, reg_measure, jitter = mocked.call_args_list[0][0]
#     assert measure.measure_id == "i1.m1"
#     assert reg_measure.measure_id == "i1.age"
#     assert jitter == 0.12
#     measure, reg_measure, jitter = mocked.call_args_list[1][0]
#     assert measure.measure_id == "i1.m1"
#     assert reg_measure.measure_id == "i1.iq"
#     assert jitter == 0.13


# def test_handle_regressions_non_continuous_or_ordinal_measure(
#     fake_phenotype_data, output_dir, fake_phenotype_data_desc_conf
# ):
#     reg = GPFConfigParser.load_config(
#         fake_phenotype_data_desc_conf, pheno_conf_schema
#     )
#     prep = PreparePhenoBrowserBase(
#         "fake", fake_phenotype_data, output_dir, reg
#     )
#     regressand_categorical = fake_phenotype_data.get_measure("i1.m5")
#     regressand_raw = fake_phenotype_data.get_measure("i1.m6")

#     with pytest.raises(StopIteration):
#         next(prep.handle_regressions(regressand_categorical))

#     with pytest.raises(StopIteration):
#         next(prep.handle_regressions(regressand_raw))


# def test_handle_regressions_regressand_is_regressor(
#     fake_phenotype_data, output_dir, fake_phenotype_data_desc_conf
# ):
#     reg = GPFConfigParser.load_config(
#         fake_phenotype_data_desc_conf, pheno_conf_schema
#     )
#     prep = PreparePhenoBrowserBase(
#         "fake", fake_phenotype_data, output_dir, reg
#     )
#     regressand = fake_phenotype_data.get_measure("i1.age")

#     with pytest.raises(StopIteration):
#         next(prep.handle_regressions(regressand))


# # def test_handle_regressions_default_jitter(
# #     mocker, fake_phenotype_data, output_dir, fake_phenotype_data_desc_conf
# # ):
# #     def fake_build_regression(*args):
# #         return {"pvalue_regression_male": 0, "pvalue_regression_female": 0}

# #     mocked = mocker.patch(
# #         "dae.pheno_browser.prepare_data."
# #         "PreparePhenoBrowserBase.build_regression",
# #         side_effect=fake_build_regression,
# #     )

# #     reg = GPFConfigParser.load_config(
# #         fake_phenotype_data_desc_conf, pheno_conf_schema
# #     )
# #     prep = PreparePhenoBrowserBase(
# #         "fake", fake_phenotype_data, output_dir, reg
# #     )
# #     regressand = fake_phenotype_data.get_measure("i1.m1")
# #     for i in prep.handle_regressions(regressand):
# #         pass

# #     mocked.assert_called()
# #     measure, reg_measure, jitter = mocked.call_args_list[0][0]
# #     assert jitter == 0.12
# #     measure, reg_measure, jitter = mocked.call_args_list[1][0]
# #     assert jitter == 0.13
