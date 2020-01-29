import pytest
from dae.studies.tests.conftest import genotype_data_groups_dir


def test_genotype_data_group_configs_simple(genotype_data_group_configs):
    assert genotype_data_group_configs is not None


@pytest.mark.parametrize('option_name,expected_value', [
    ('name', 'QUADS_COMPOSITE'),
    ('id', 'quads_composite_ds'),
    ('description', 'QUADS COMPOSITE DESCRIPTION'),
    ('studies', ['quads_in_child', 'quads_in_parent']),

    ('phenotypeTool', None),
    ('phenotypeBrowser', None),
    ('year', None),
    ('pub_med', None),
])
def test_genotype_data_group_quads_composite_dict(
        quads_composite_genotype_data_group_config,
        option_name,
        expected_value):

    assert quads_composite_genotype_data_group_config is not None
    config = quads_composite_genotype_data_group_config

    assert getattr(config, option_name) == expected_value


@pytest.mark.parametrize('option_name,expected_value', [
    ('name', 'QUADS_COMPOSITE'),
    ('id', 'quads_composite_ds'),
    ('description', 'QUADS COMPOSITE DESCRIPTION'),
    ('studies', ['quads_in_child', 'quads_in_parent']),

    ('phenotype_tool', None),
    ('phenotype_browser', None),
    ('year', None),
    ('pub_med', None),
])
def test_genotype_data_group_quads_composite_attr(
        quads_composite_genotype_data_group_config,
        option_name,
        expected_value):

    assert quads_composite_genotype_data_group_config is not None
    config = quads_composite_genotype_data_group_config

    assert getattr(config, option_name) == expected_value


def test_composite_genotype_data_group_config_people_group(
        composite_dataset_config):
    assert composite_dataset_config is not None
    assert composite_dataset_config.people_group_config is None


def test_composite_genotype_data_group_config_genotype_browser(
        composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.genotype_browser is None


def test_composite_genotype_data_group_config_enrichment_tool(
        composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.enrichment_tool is None


def test_composite_genotype_data_group_config_people_group_no_overwrite(
        quads_composite_genotype_data_group_config):
    assert quads_composite_genotype_data_group_config is not None

    assert quads_composite_genotype_data_group_config.people_group_config \
        is None


def test_composite_genotype_data_group_config_genotype_browser_overwrite(
        quads_composite_genotype_data_group_config, variants_db_fixture):

    assert quads_composite_genotype_data_group_config is not None

    study_config = variants_db_fixture.get_study_config(
        quads_composite_genotype_data_group_config.studies[0])

    assert quads_composite_genotype_data_group_config.genotype_browser.enabled is True
    genotype_browser_config = \
        quads_composite_genotype_data_group_config.genotype_browser
    assert genotype_browser_config is not None

    assert study_config.genotype_browser != genotype_browser_config

    download_columns = genotype_browser_config.download_columns
    print(download_columns)

    assert download_columns == [
        'family', 'phenotype', 'variant', 'best', 'fromparent', 'inchild',
        'effect', 'count', 'geneeffect', 'effectdetails'
    ]


def test_genotype_data_group_quads_work_dir(
        quads_composite_genotype_data_group_config):

    assert quads_composite_genotype_data_group_config is not None
    config = quads_composite_genotype_data_group_config

    assert config.work_dir == \
        genotype_data_groups_dir()
