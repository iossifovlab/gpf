import pytest


pytestmark = pytest.mark.usefixtures('gene_info_cache_dir', 'calc_gene_sets')


def name_in_gene_sets(gene_sets, name, count=None):
    for gene_set in gene_sets:
        if gene_set['name'] == name:
            print(gene_set)
            if count is not None:
                if gene_set['count'] == count:
                    return True
                else:
                    return False
            return True

    return False


def test_denovo_gene_sets_exist(denovo_gene_sets_facade):
    denovo = denovo_gene_sets_facade.has_denovo_gene_set('denovo')
    assert denovo


def test_main_gene_sets_missing(denovo_gene_sets_facade):
    with pytest.raises(AssertionError):
        denovo_gene_sets_facade.has_denovo_gene_set('main')


def test_get_all_collections_descriptions(denovo_gene_sets_facade):
    gene_sets_collections = \
        denovo_gene_sets_facade.get_collections_descriptions()
    assert gene_sets_collections['desc'] == 'Denovo'
    assert gene_sets_collections['name'] == 'denovo'
    assert gene_sets_collections['format'] == ['key', ' (|count|)']
    assert len(gene_sets_collections['types']) == 4


def test_get_f4_collections_descriptions(denovo_gene_sets_facade):
    gene_sets_collections = \
        denovo_gene_sets_facade.get_collections_descriptions(
            permitted_datasets=['f4_trio'])
    assert gene_sets_collections['desc'] == 'Denovo'
    assert gene_sets_collections['name'] == 'denovo'
    assert gene_sets_collections['format'] == ['key', ' (|count|)']
    assert len(gene_sets_collections['types']) == 1
    assert gene_sets_collections['types'][0]['datasetId'] == 'f4_trio'
    assert gene_sets_collections['types'][0]['datasetName'] == 'f4_trio'
    assert gene_sets_collections['types'][0]['peopleGroupId'] == 'phenotype'
    assert gene_sets_collections['types'][0]['peopleGroupName'] == 'Phenotype'
    assert len(gene_sets_collections['types'][0]['peopleGroupLegend']) == 6


@pytest.mark.parametrize('denovo_gene_set_id,people_groups,count', [
    ('Missense', ['autism'], 1),
    ('Missense', ['autism', 'unaffected'], 1),
    ('Synonymous', ['autism'], 1),
    ('Synonymous', ['unaffected'], 1),
    ('Synonymous', ['autism', 'unaffected'], 2),
])
def test_get_denovo_gene_set_f4(
        denovo_gene_sets_facade, denovo_gene_set_id, people_groups, count):
    dgs = denovo_gene_sets_facade.get_denovo_gene_set(
        'denovo', denovo_gene_set_id,
        {'f4_trio': {'phenotype': people_groups}})

    assert dgs is not None
    assert dgs['count'] == count
    assert dgs['name'] == denovo_gene_set_id
    assert dgs['desc'] == '{} (f4_trio:phenotype:{})'.format(
        denovo_gene_set_id, ','.join(people_groups))


@pytest.mark.parametrize('denovo_gene_set_id,people_groups', [
    ('LGDs', ['autism']),
    ('LGDs', ['unaffected']),
    ('LGDs', ['autism', 'unaffected']),
    ('Missense', ['unaffected']),
])
def test_get_denovo_gene_set_f4_empty(
        denovo_gene_sets_facade, denovo_gene_set_id, people_groups):
    dgs = denovo_gene_sets_facade.get_denovo_gene_set(
        'denovo', denovo_gene_set_id,
        {'f4_trio': {'phenotype': people_groups}})

    assert dgs is None


def test_get_denovo_gene_sets_f4_autism(denovo_gene_sets_facade):
    dgs = denovo_gene_sets_facade.get_denovo_gene_sets(
        'denovo', {'f4_trio': {'phenotype': ['autism']}})

    assert dgs is not None
    assert len(dgs) == 4
    assert name_in_gene_sets(dgs, 'Synonymous', 1)
    assert name_in_gene_sets(dgs, 'Missense', 1)
    assert name_in_gene_sets(dgs, 'Missense.Recurrent', 1)
    assert name_in_gene_sets(dgs, 'Missense.Female', 1)


def test_get_denovo_gene_sets_f4_unaffected(denovo_gene_sets_facade):
    dgs = denovo_gene_sets_facade.get_denovo_gene_sets(
        'denovo', {'f4_trio': {'phenotype': ['unaffected']}})

    assert dgs is not None
    assert len(dgs) == 1
    assert name_in_gene_sets(dgs, 'Synonymous', 1)


def test_get_denovo_gene_sets_f4_autism_unaffected(denovo_gene_sets_facade):
    dgs = denovo_gene_sets_facade.get_denovo_gene_sets(
        'denovo', {'f4_trio': {'phenotype': ['autism', 'unaffected']}})

    assert dgs is not None
    assert len(dgs) == 4
    assert name_in_gene_sets(dgs, 'Synonymous', 2)
    assert name_in_gene_sets(dgs, 'Missense', 1)
    assert name_in_gene_sets(dgs, 'Missense.Recurrent', 1)
    assert name_in_gene_sets(dgs, 'Missense.Female', 1)


def test_all_denovo_gene_set_ids(denovo_gene_sets_facade):
    assert sorted(denovo_gene_sets_facade.get_all_denovo_gene_set_ids()) == \
        sorted(['f1_group', 'f2_group', 'f3_group', 'f4_trio'])


def test_build_load_denovo_gene_set_cache(denovo_gene_sets_facade):
    dgs = denovo_gene_sets_facade.get_denovo_gene_sets(
        'denovo', {'f4_trio': {'phenotype': ['autism', 'unaffected']}})

    assert dgs is not None
    assert len(dgs) == 4

    denovo_gene_sets_facade.build_cache(['f4_trio'])
    denovo_gene_sets_facade._denovo_gene_set_cache = {}
    denovo_gene_sets_facade._denovo_gene_set_config_cache = {}

    dgs = denovo_gene_sets_facade.get_denovo_gene_sets(
        'denovo', {'f4_trio': {'phenotype': ['autism', 'unaffected']}})

    assert dgs is not None
    assert len(dgs) == 4
