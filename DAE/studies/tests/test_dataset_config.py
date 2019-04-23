import pytest

import sys


def test_dataset_definitions_simple(dataset_definitions):
    assert dataset_definitions is not None


@pytest.mark.parametrize("option_name,expected_value", [
    ("name", "QUADS_COMPOSITE"),
    ("id", "quads_composite_ds"),
    ("description", "QUADS COMPOSITE DESCRIPTION"),
    ("studies", ['quads_in_child', 'quads_in_parent']),
    # ("phenotypes", {'autism', 'schizophrenia', 'epilepsy'}),

    ("phenotypeGenotypeTool", False),
    ("phenotypeBrowser", False),
    ("year", ""),
    ("years", []),
    ("pub_med", ""),
    ("pub_meds", [])
])
def test_dataset_quads_composite_dict(
        quads_composite_dataset_config, option_name, expected_value):

    assert quads_composite_dataset_config is not None
    config = quads_composite_dataset_config

    assert config[option_name] == expected_value


@pytest.mark.parametrize("option_name,expected_value", [
    ("name", "QUADS_COMPOSITE"),
    ("id", "quads_composite_ds"),
    ("description", "QUADS COMPOSITE DESCRIPTION"),
    ("studies", ['quads_in_child', 'quads_in_parent']),
    # ("phenotypes", {'autism', 'schizophrenia', 'epilepsy'}),

    ("phenotypeGenotypeTool", False),
    ("phenotypeBrowser", False),

    ("phenotype_genotype_tool", False),
    ("phenotype_browser", False),
    ("year", ""),
    ("years", []),
    ("pub_med", ""),
    ("pub_meds", [])
])
def test_dataset_quads_composite_attr(
        quads_composite_dataset_config, option_name, expected_value):

    assert quads_composite_dataset_config is not None
    config = quads_composite_dataset_config

    assert getattr(config, option_name) == expected_value


@pytest.mark.xfail(sys.version_info < (3,), reason="requires python3")
def test_composite_dataset_config_people_group(composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.genotype_browser is not None
    assert composite_dataset_config.genotype_browser.people_group is not None
    people_group = composite_dataset_config.genotype_browser.people_group

    assert len(people_group) == 1
    pg = people_group[0]

    assert pg.name == 'Phenotype'


@pytest.mark.xfail
def test_composite_dataset_config_genotype_browser(composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.genotype_browser is not None
    genotype_browser = composite_dataset_config.genotype_browser

    download_columns = genotype_browser.download_columns
    assert download_columns.to_list() == \
        ['family', 'phenotype', 'variant', 'best', 'fromparent',
         'inchild', 'effect', 'count', 'geneeffect', 'effectdetails',
         'weights', 'freq']


def test_composite_dataset_config_enrichment_tool(composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.enrichment_tool is not None

    enrichment_tool = composite_dataset_config.enrichment_tool

    assert enrichment_tool.selector == 'phenotype'
    assert enrichment_tool.study_types == 'WE'


def test_composite_dataset_config_authorized_groups(composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config['authorizedGroups'] is not None
    assert composite_dataset_config['authorizedGroups'].to_list() == \
        ['any_user']

    assert composite_dataset_config.authorized_groups is not None
    assert composite_dataset_config.authorized_groups.to_list() == \
        ['any_user']


def test_composite_dataset_config_people_group_overwrite(
        quads_composite_dataset_config):
    assert quads_composite_dataset_config is not None

    assert quads_composite_dataset_config.genotype_browser is not None
    assert quads_composite_dataset_config.genotype_browser.people_group \
        is not None
    people_group = quads_composite_dataset_config.genotype_browser.people_group

    assert len(people_group) == 1
    pg = people_group[0]
    assert pg.name == 'Phenotype'
    assert len(pg['values']) == 6


def test_composite_dataset_config_genotype_browser_overwrite(
        quads_composite_dataset_config):

    assert quads_composite_dataset_config is not None

    study_config = quads_composite_dataset_config.studies_configs[0]

    assert quads_composite_dataset_config.genotype_browser is not None
    genotype_browser = quads_composite_dataset_config.genotype_browser

    assert study_config.genotype_browser != genotype_browser

    download_columns = genotype_browser.download_columns
    print(download_columns)

    assert download_columns.to_list() == \
        ['family', 'phenotype', 'variant', 'best', 'fromparent',
         'inchild', 'effect', 'count', 'geneeffect', 'effectdetails']
