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
    assert study_config.year is None


def test_quads_f1_config_genotype_storage(quads_f1_config):
    assert quads_f1_config is not None

    assert quads_f1_config.genotype_storage.id == 'genotype_filesystem'


@pytest.mark.parametrize('option_name,expected_value', [
    ('name', 'QUADS_F1'),
    ('id', 'quads_f1'),
    ('description', 'QUADS F1'),

    ('phenotype_tool', True),
    ('phenotype_browser', False),
    ('phenotype_data', 'quads_f1'),
    ('year', None),
    ('pub_med', None),
])
def test_quads_f1_config_attr_access(
        quads_f1_config, option_name, expected_value):
    assert quads_f1_config is not None

    assert getattr(quads_f1_config, option_name) == expected_value


@pytest.mark.parametrize('option_name,expected_value', [
    ('has_present_in_child', False),
    ('has_present_in_parent', False),
    ('has_family_filters', False),
    ('has_pedigree_selector', True),
    ('has_cnv', None),
    ('has_complex', None),
    ('has_study_filters', None),
])
def test_quads_f1_config_genotype_browser(
        quads_f1_config, option_name, expected_value):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert getattr(genotype_browser_config, option_name) == expected_value


def test_quads_f1_config_genotype_browser_pheno_filters(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser

    first = genotype_browser_config.pheno_filters[0]._asdict()
    print(first)
    first["filter"] = list(map(lambda x: x._asdict(), first["filter"]))
    assert first == {
        'name': 'Categorical',
        'measure_type': 'categorical',
        'filter': [
            {
                'filter_type': 'single',
                'role': 'prb',
                'measure': 'instrument1.categorical'
            }
        ]
    }
    second = genotype_browser_config.pheno_filters[1]._asdict()
    second["filter"] = list(map(lambda x: x._asdict(), second["filter"]))
    assert second == {
        'name': 'Continuous',
        'measure_type': 'continuous',
        'filter': [
            {
                'filter_type': 'single',
                'role': 'prb',
                'measure': 'instrument1.continuous'
            }
        ]
    }


def test_quads_f1_config_genotype_browser_present_in_role(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert len(genotype_browser_config.present_in_role) == 2
    assert genotype_browser_config.present_in_role[0].section_id() == 'prb'
    assert genotype_browser_config.present_in_role[0].name == \
        'Present in Proband and Sibling'
    assert len(genotype_browser_config.present_in_role[0].roles) == 2
    assert genotype_browser_config.present_in_role[0].roles[0] == 'prb'
    assert genotype_browser_config.present_in_role[0].roles[1] == 'sib'

    assert genotype_browser_config.present_in_role[1].section_id() == 'parent'
    assert genotype_browser_config.present_in_role[1].name == \
        'Parents'
    assert len(genotype_browser_config.present_in_role[1].roles) == 2
    assert genotype_browser_config.present_in_role[1].roles[0] == 'mom'
    assert genotype_browser_config.present_in_role[1].roles[1] == 'dad'


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
                'name': None,
                'id': 'effect.genes',
                'format': '%s'
            }
        ]),
        ('best', 'family genotype', 'bestSt', []),
    ]
)
def test_quads_f1_config_genotype_browser_columns(
        quads_f1_config, option_name, expected_name, expected_source,
        expected_slots):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert len(genotype_browser_config.genotype) == 14

    genotype_column = list(filter(
        lambda gc: gc.section_id() == option_name,
        genotype_browser_config.genotype
    ))

    assert len(genotype_column) == 1
    genotype_column = genotype_column[0]

    assert genotype_column.section_id() == option_name
    assert genotype_column.name == expected_name
    assert genotype_column.source == expected_source

    if genotype_column.slots:
        assert len(genotype_column.slots) == len(expected_slots)

        for gc_slot, e_slot in zip(genotype_column.slots, expected_slots):
            assert gc_slot.source == e_slot['source']
            assert gc_slot.name == e_slot['name']
            assert gc_slot.format == e_slot['format']


@pytest.mark.parametrize(
    'option_name,expected_name,expected_source,expected_slots', [
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
def test_quads_f1_config_genotype_browser_pheno_columns(
        quads_f1_config, option_name, expected_name, expected_source,
        expected_slots):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert len(genotype_browser_config.genotype) == 14

    genotype_column = list(filter(
        lambda gc: gc.section_id() == option_name,
        genotype_browser_config.pheno
    ))

    assert len(genotype_column) == 1
    genotype_column = genotype_column[0]

    assert genotype_column.section_id() == option_name
    assert genotype_column.name == expected_name
    assert genotype_column.source == expected_source

    if genotype_column.slots:
        assert len(genotype_column.slots) == len(expected_slots)

        for gc_slot, e_slot in zip(genotype_column.slots, expected_slots):
            assert gc_slot.measure == e_slot['measure']
            assert gc_slot.name == e_slot['name']
            assert gc_slot.format == e_slot['format']


def test_quads_f1_files_and_tables(quads_f1_config):
    assert quads_f1_config.genotype_storage.files.variants[0].path.endswith(
        'data/quads_f1.vcf')
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        'data/quads_f1.ped')
    # assert quads_f1_config.files.denovo[0].path.endswith(
    #     'data/quads_f1_denovo.tsv')

    # assert quads_f1_config.tables.variant == 'quads_f1_variant'
    # assert quads_f1_config.tables.pedigree == 'quads_f1_pedigree'


def test_quads_f1_config_work_dir(quads_f1_config):
    assert quads_f1_config.work_dir == \
        os.path.join(studies_dir(), 'quads_f1')


def test_quads_f1_config_files(quads_f1_config):
    assert quads_f1_config.genotype_storage.files is not None
    assert quads_f1_config.genotype_storage.files.pedigree is not None
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        '/data/quads_f1.ped')
    assert len(quads_f1_config.genotype_storage.files.pedigree.params) == 3
