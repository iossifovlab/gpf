import pytest


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


def test_quads_f1_enrichment_tool(quads_f1_config):
    print(quads_f1_config.keys())
    print(quads_f1_config['enrichmentTool'])
