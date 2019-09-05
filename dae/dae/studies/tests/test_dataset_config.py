import pytest


def test_dataset_configs_simple(dataset_configs):
    assert dataset_configs is not None


@pytest.mark.parametrize("option_name,expected_value", [
    ("name", "QUADS_COMPOSITE"),
    ("id", "quads_composite_ds"),
    ("description", "QUADS COMPOSITE DESCRIPTION"),
    ("studies", ['quads_in_child', 'quads_in_parent']),

    ("phenotypeTool", False),
    ("phenotypeBrowser", False),
    ("year", ""),
    # ("years", []),
    # ("pub_med", ""),
    # ("pub_meds", [])
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

    ("phenotypeTool", False),
    ("phenotypeBrowser", False),

    ("phenotype_tool", False),
    ("phenotype_browser", False),
    ("year", ""),
    # ("years", []),
    # ("pub_med", ""),
    # ("pub_meds", [])
])
def test_dataset_quads_composite_attr(
        quads_composite_dataset_config, option_name, expected_value):

    assert quads_composite_dataset_config is not None
    config = quads_composite_dataset_config

    assert getattr(config, option_name) == expected_value


def test_composite_dataset_config_people_group(composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.people_group_config is not None
    assert composite_dataset_config.people_group_config.people_group \
        is not None
    people_group = composite_dataset_config.people_group_config.people_group

    assert len(people_group) == 1
    pg = people_group[0]

    assert pg.name == 'Phenotype'


# FIXME: this was causing segmentation fault while testing
# @pytest.mark.xfail
# def test_composite_dataset_config_genotype_browser(composite_dataset_config):
#     assert composite_dataset_config is not None

#     assert composite_dataset_config.genotype_browser is True
#     genotype_browser_config = composite_dataset_config.genotype_browser_config
#     assert genotype_browser_config is not None

#     download_columns = genotype_browser_config.download_columns
#     assert download_columns.to_list() == \
#         ['family', 'phenotype', 'variant', 'best', 'fromparent',
#          'inchild', 'effect', 'count', 'geneeffect', 'effectdetails',
#          'weights', 'freq']


def test_composite_dataset_config_enrichment_tool(composite_dataset_config):
    assert composite_dataset_config is not None

    assert composite_dataset_config.enrichment_tool is True


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

    assert quads_composite_dataset_config.people_group_config is not None
    assert quads_composite_dataset_config.people_group_config.people_group \
        is not None
    people_group = quads_composite_dataset_config. \
        people_group_config.people_group

    assert len(people_group) == 1
    pg = people_group[0]
    assert pg.name == 'Phenotype'
    assert len(pg['values']) == 6


def test_composite_dataset_config_genotype_browser_overwrite(
        quads_composite_dataset_config, variants_db_fixture):

    assert quads_composite_dataset_config is not None

    study_config = variants_db_fixture.get_study_config(
        quads_composite_dataset_config.studies[0])

    assert quads_composite_dataset_config.genotype_browser is True
    genotype_browser_config = \
        quads_composite_dataset_config.genotype_browser_config
    assert genotype_browser_config is not None

    assert study_config.genotype_browser_config != genotype_browser_config

    download_columns = genotype_browser_config.download_columns
    print(download_columns)

    assert download_columns == \
        ['family', 'phenotype', 'variant', 'best', 'fromparent',
         'inchild', 'effect', 'count', 'geneeffect', 'effectdetails']
