import pytest


def test_study_config_simple(study_definitions):
    assert study_definitions is not None
    assert study_definitions.study_ids


def test_study_config_year(study_definitions):
    study_config = study_definitions.get_study_config('inheritance_trio')
    assert study_config is not None
    assert study_config.year == ''


@pytest.mark.parametrize("option_name,expected_value", [
    ("file_format", "vcf"),
    ("phenotypes", {"autism"}),
    ("name", "QUADS_F1"),
    ("id", "quads_f1"),
    ("description", "QUADS F1"),
    ("phenotypeGenotypeTool", True),
    ("phenotypeBrowser", False),
    ("phenoDB", ""),
])
def test_quads_f1_config_dict(quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert quads_f1_config[option_name] == expected_value


@pytest.mark.parametrize("option_name,expected_value", [
    ("file_format", "vcf"),
    ("phenotypes", {"autism"}),
    ("name", "QUADS_F1"),
    ("id", "quads_f1"),
    ("description", "QUADS F1"),
    ("phenotypeGenotypeTool", True),
    ("phenotypeBrowser", False),

    ("phenotype_genotype_tool", True),
    ("phenotype_browser", False),
    ("pheno_db", ''),
    ("year", ''),
    ("pub_med", ''),
    ("years", []),
    ("pub_meds", []),
])
def test_quads_f1_config_attr(quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert getattr(quads_f1_config, option_name) == expected_value


@pytest.mark.parametrize("option_name,expected_value", [
    ("hasPresentInChild", False),
    ("hasPresentInParent", False),
    ("hasFamilyFilters", False),
    ("hasPedigreeSelector", True),
    ("hasCNV", False),
    ("hasComplex", False),
    ("hasStudyFilters", True),
    ("phenoFilters", None),
])
def test_quads_f1_config_genotype_browser(
        quads_f1_config, option_name, expected_value):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    assert genotype_browser_config[option_name] == expected_value


def test_quads_f1_config_genotype_browser_present_in_role(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    assert len(genotype_browser_config['presentInRole']) == 1
    assert genotype_browser_config['presentInRole'][0].id == 'prb'
    assert genotype_browser_config['presentInRole'][0].name == \
        'Present in Probant and Sibling'
    assert len(genotype_browser_config['presentInRole'][0].roles) == 2
    assert genotype_browser_config['presentInRole'][0].roles[0] == 'Proband'
    assert genotype_browser_config['presentInRole'][0].roles[1] == 'Sibling'


@pytest.mark.parametrize(
    "option_name,expected_name,expected_source,expected_slots", [
        ("genotype", "genotype", "pedigree", [
            {'source': "inChS", 'name': 'in child', 'id': 'inChS',
             'format': '%s'},
            {'source': "fromParentS", 'name': 'from parent',
             'id': 'fromParentS', 'format': '%s'}
        ]),
        ("effect", "effect", None, [
            {'source': "worstEffect", 'name': 'worst effect type',
             'id': 'worstEffect', 'format': '%s'},
            {'source': "genes", 'name': 'genes', 'id': 'genes',
             'format': '%s'}
        ]),
        ("best", "family genotype", "bestSt", []),
    ]
)
def test_quads_f1_config_genotype_browser_genotype_column(
        quads_f1_config, option_name, expected_name, expected_source,
        expected_slots):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    genotype_column = list(filter(
        lambda gc: gc['id'] == option_name,
        genotype_browser_config['genotypeColumns']
    ))

    assert len(genotype_column) == 1
    genotype_column = genotype_column[0]

    assert genotype_column['id'] == option_name
    assert genotype_column['name'] == expected_name
    assert genotype_column['source'] == expected_source

    assert len(genotype_column['slots']) == len(expected_slots)

    for gc_slot, e_slot in zip(genotype_column['slots'], expected_slots):
        assert gc_slot['source'] == e_slot['source']
        assert gc_slot['name'] == e_slot['name']
        assert gc_slot['id'] == e_slot['id']
        assert gc_slot['format'] == e_slot['format']
