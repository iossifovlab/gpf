import pytest


def test_dataset_definitions_simple(dataset_definitions):
    assert dataset_definitions is not None


@pytest.mark.parametrize("option_name,expected_value", [
    ("name", "QUADS_COMPOSITE"),
    ("id", "quads_composite"),
    ("description", "QUADS COMPOSITE DESCRIPTION"),
    ("studies", ['quads_in_child', 'quads_in_parent']),
    ("phenotypes", {'autism', 'schizophrenia', 'epilepsy'}),

    ("phenotypeGenotypeTool", True),
    ("phenotypeBrowser", False),
])
def test_dataset_quads_composite_dict(
        quads_composite_dataset_config, option_name, expected_value):

    assert quads_composite_dataset_config is not None
    config = quads_composite_dataset_config

    assert config[option_name] == expected_value


@pytest.mark.parametrize("option_name,expected_value", [
    ("name", "QUADS_COMPOSITE"),
    ("id", "quads_composite"),
    ("description", "QUADS COMPOSITE DESCRIPTION"),
    ("studies", ['quads_in_child', 'quads_in_parent']),
    ("phenotypes", {'autism', 'schizophrenia', 'epilepsy'}),

    ("phenotypeGenotypeTool", True),
    ("phenotypeBrowser", False),

    ("phenotype_genotype_tool", True),
    ("phenotype_browser", False),
])
def test_dataset_quads_composite_attr(
        quads_composite_dataset_config, option_name, expected_value):

    assert quads_composite_dataset_config is not None
    config = quads_composite_dataset_config

    print(config.phenotype_genotype_tool)
    print(config.phenotype_browser)
    assert getattr(config, option_name) == expected_value
