import os
import pytest
from dae.studies.tests.conftest import studies_dir
from box import Box


def test_study_config_simple(genotype_data_study_configs):
    assert genotype_data_study_configs is not None
    assert list(genotype_data_study_configs.keys())


def test_study_config_year(genotype_data_study_configs):
    study_config = genotype_data_study_configs.get('inheritance_trio')
    assert study_config is not None
    assert study_config.year == ''


@pytest.mark.parametrize('option_name,expected_value', [
    ('genotype_storage', 'genotype_filesystem'),
    ('name', 'QUADS_F1'),
    ('id', 'quads_f1'),
    ('description', 'QUADS F1'),
    ('phenotypeTool', True),
    ('phenotypeBrowser', False),
    ('phenotypeData', 'quads_f1'),

])
def test_quads_f1_config_dict_access(
        quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert quads_f1_config[option_name] == expected_value


@pytest.mark.parametrize('option_name,expected_value', [
    ('genotype_storage', 'genotype_filesystem'),
    ('name', 'QUADS_F1'),
    ('id', 'quads_f1'),
    ('description', 'QUADS F1'),
    ('phenotypeTool', True),
    ('phenotypeBrowser', False),
    ('phenotypeData', 'quads_f1'),

    ('phenotype_tool', True),
    ('phenotype_browser', False),
    ('phenotype_data', 'quads_f1'),
    ('year', ''),
    ('pub_med', ''),
    ('years', []),
    ('pub_meds', []),
])
def test_quads_f1_config_attr_access(
        quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert getattr(quads_f1_config, option_name) == expected_value


@pytest.mark.parametrize('option_name,expected_value', [
    ('hasPresentInChild', False),
    ('hasPresentInParent', False),
    ('hasFamilyFilters', False),
    ('hasPedigreeSelector', True),
    ('hasCNV', False),
    ('hasComplex', False),
    ('hasStudyFilters', True),
])
def test_quads_f1_config_genotype_browser(
        quads_f1_config, option_name, expected_value):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    assert genotype_browser_config[option_name] == expected_value


def test_quads_f1_config_genotype_browser_pheno_filters(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    assert genotype_browser_config['phenoFilters'] == [
        Box({
            'id': 'Categorical',
            'name': 'Categorical',
            'measureType': 'categorical',
            'filter': 'single:prb:instrument1.categorical',
            'measureFilter': {
                'filterType': 'single',
                'role': 'prb',
                'measure': 'instrument1.categorical'
            }
        }),
        Box({
            'id': 'Continuous',
            'name': 'Continuous',
            'measureType': 'continuous',
            'filter': 'single:prb:instrument1.continuous',
            'measureFilter': {
                'filterType': 'single',
                'role': 'prb',
                'measure': 'instrument1.continuous'
            }
        }),
    ]


def test_quads_f1_config_genotype_browser_present_in_role(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    assert len(genotype_browser_config['presentInRole']) == 2
    assert genotype_browser_config['presentInRole'][0].id == 'prb'
    assert genotype_browser_config['presentInRole'][0].name == \
        'Present in Proband and Sibling'
    assert len(genotype_browser_config['presentInRole'][0].roles) == 2
    assert genotype_browser_config['presentInRole'][0].roles[0] == 'Proband'
    assert genotype_browser_config['presentInRole'][0].roles[1] == 'Sibling'

    assert genotype_browser_config['presentInRole'][1].id == 'parent'
    assert genotype_browser_config['presentInRole'][1].name == \
        'Parents'
    assert len(genotype_browser_config['presentInRole'][1].roles) == 2
    assert genotype_browser_config['presentInRole'][1].roles[0] == 'Mom'
    assert genotype_browser_config['presentInRole'][1].roles[1] == 'Dad'


@pytest.mark.parametrize(
    'option_name,expected_name,expected_source,expected_slots', [
        ('genotype', 'genotype', 'pedigree', [
            {
                'source': 'inChS',
                'name': 'in child',
                'id': 'genotype.in child',
                'format': '%s'
            },
            {
                'source': 'fromParentS',
                'name': 'from parent',
                'id': 'genotype.from parent',
                'format': '%s'
            }
        ]),
        ('effect', 'effect', None, [
            {
                'source': 'worstEffect',
                'name': 'worst effect type',
                'id': 'effect.worst effect type',
                'format': '%s'
            },
            {
                'source': 'genes',
                'name': 'genes',
                'id': 'effect.genes',
                'format': '%s'
            }
        ]),
        ('best', 'family genotype', 'bestSt', []),
        ('continuous', 'Continuous', None, [
            {
                'id': 'continuous.Continuous',
                'name': 'Continuous',
                'role': 'prb',
                'measure': 'instrument1.continuous',
                'source': 'prb.instrument1.continuous',
                'format': '%s'
            }
        ]),
        ('categorical', 'Categorical', None, [
            {
                'id': 'categorical.Categorical',
                'name': 'Categorical',
                'role': 'prb',
                'measure': 'instrument1.categorical',
                'source': 'prb.instrument1.categorical',
                'format': '%s'
            }
        ]),
        ('ordinal', 'Ordinal', None, [
            {
                'id': 'ordinal.Ordinal',
                'name': 'Ordinal',
                'role': 'prb',
                'measure': 'instrument1.ordinal',
                'source': 'prb.instrument1.ordinal',
                'format': '%s'
            }
        ]),
        ('raw', 'Raw', None, [
            {
                'id': 'raw.Raw',
                'name': 'Raw',
                'role': 'prb',
                'measure': 'instrument1.raw',
                'source': 'prb.instrument1.raw',
                'format': '%s'
            }
        ]),
    ]
)
def test_quads_f1_config_genotype_browser_columns(
        quads_f1_config, option_name, expected_name, expected_source,
        expected_slots):
    genotype_browser_config = quads_f1_config.genotype_browser_config

    assert len(genotype_browser_config['genotypeColumns']) == 17

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


def test_quads_f1_files_and_tables(quads_f1_config):
    assert quads_f1_config.files.vcf[0].path.endswith('data/quads_f1.vcf')
    assert quads_f1_config.files.pedigree.path.endswith('data/quads_f1.ped')
    # assert quads_f1_config.files.denovo[0].path.endswith(
    #     'data/quads_f1_denovo.tsv')

    assert quads_f1_config.tables.variant == 'quads_f1_variant'
    assert quads_f1_config.tables.pedigree == 'quads_f1_pedigree'


def test_quads_f1_config_work_dir(quads_f1_config):
    assert quads_f1_config['work_dir'] == \
        os.path.join(studies_dir(), 'quads_f1')


def test_quads_f1_config_files(quads_f1_config):
    assert quads_f1_config['files'] is not None
    assert quads_f1_config.files.pedigree is not None
    assert quads_f1_config.files.pedigree.path.endswith('/data/quads_f1.ped')
    assert len(quads_f1_config.files.pedigree.params) == 6


def test_quads_f1_config_tables(quads_f1_config):
    assert quads_f1_config['tables'] is not None

    assert quads_f1_config.tables.pedigree == 'quads_f1_pedigree'
    assert quads_f1_config.tables.variant == 'quads_f1_variant'
