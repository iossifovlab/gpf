import pytest

# import os

# ALL_STUDIES = {'test', 'test_enabled_true', 'autism_and_epilepsy'}


# def get_study(study_configs, study_name):
#     return next(
#         study for study in study_configs
#         if study.study_name == study_name)


# def test_configs_is_read_properly(study_configs):
#     assert study_configs is not None


# def test_fixture_configs_have_correct_studies(study_configs):
#     studies = list(study.study_name for study in study_configs)
#     assert set(studies) == ALL_STUDIES


# def test_prefix_gets_default_location_as_config(study_configs):
#     test_study_config = get_study(study_configs, 'test')

#     assert test_study_config is not None

#     assert os.path.isabs(test_study_config.prefix)


# def test_enabled_option(study_configs):
#     studies = set([study.study_name for study in study_configs])

#     assert studies == ALL_STUDIES
#     assert 'test_enabled_false' not in studies


# def test_multiple_phenotypes_are_loaded(study_configs):
#     study = get_study(study_configs, 'autism_and_epilepsy')
#     print(study)

#     assert study.phenotypes == {'autism', 'epilepsy'}

def test_study_config_simple(study_definitions):
    print(study_definitions)
    print(study_definitions.get_all_study_names())


def test_study_config_year(study_definitions):
    study_config = study_definitions.get_study_config('inheritance_trio')
    assert study_config is not None
    print([study_config.year])
    assert study_config.year == ''


@pytest.mark.parametrize("option_name,expected_value", [
    ("type", "vcf"),
    ("phenotypes", {"autism"}),
    ("name", "QUADS_F1"),
    ("id", "quads_f1"),
    ("description", "QUADS F1"),
    ("phenotypeGenotypeTool", True),
    ("phenotypeBrowser", False),
    # ("peopleGroup.phenotype.name", "Phenotype"),
    ("phenoDB", ""),
])
def test_quads_f1_config_dict(quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert quads_f1_config[option_name] == expected_value


@pytest.mark.parametrize("option_name,expected_value", [
    ("type", "vcf"),
    ("phenotypes", {"autism"}),
    ("name", "QUADS_F1"),
    ("id", "quads_f1"),
    ("description", "QUADS F1"),
    ("phenotypeGenotypeTool", True),
    ("phenotypeBrowser", False),

    ("phenotype_genotype_tool", True),
    ("phenotype_browser", False),
    ("pheno_db", ''),
])
def test_quads_f1_config_attr(quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert getattr(quads_f1_config, option_name) == expected_value


def test_quads_f1_people_grouping(quads_f1_config):
    print(quads_f1_config.keys())
    print(quads_f1_config['pedigreeSelectors'])
    print(quads_f1_config['genotypeBrowser'])
