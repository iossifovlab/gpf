from dae.gene.gene_set_collections import GeneSetsDb, GeneSetsCollection
from dae.gene.gene_term import GeneTerms
from dae.gene.tests.conftest import path_to_fixtures


def test_get_gene_set_collection_ids(gene_sets_db):
    assert gene_sets_db.get_gene_set_collection_ids() == \
        {'main', 'term_curated'}


def test_get_gene_set_ids(gene_sets_db):
    assert gene_sets_db.get_gene_set_ids('main') == {'main_candidates'}


def test_get_collections_descriptions(gene_sets_db):
    assert gene_sets_db.get_collections_descriptions() == [
        {
            'desc': 'Main',
            'name': 'main',
            'format': ['key', ' (', 'count', '): ', 'desc'],
            'types': [],
        },
        {
            'desc': 'Term',
            'name': 'term_curated',
            'format': ['key', ' (', 'count', ')'],
            'types': [],
        }
    ]


def test_has_gene_sets_collection(gene_sets_db):
    assert gene_sets_db.has_gene_sets_collection('main')
    assert gene_sets_db.has_gene_sets_collection('term_curated')
    assert not gene_sets_db.has_gene_sets_collection('nonexistent_gsc')


def test_get_gene_sets_collection(gene_sets_db):
    gene_sets_db.gene_sets_collections = {}
    gsc = gene_sets_db.get_gene_sets_collection('main')
    assert gene_sets_db.has_gene_sets_collection('main')
    assert isinstance(gsc, GeneSetsCollection)


def test_get_gene_sets(gene_sets_db):
    gene_sets = gene_sets_db.get_gene_sets('main')

    assert len(gene_sets) == 1
    gene_set = gene_sets[0]

    assert gene_set is not None
    assert gene_set['name'] == 'main_candidates'
    assert gene_set['count'] == 9
    assert gene_set['desc'] == 'Main Candidates'


def test_get_gene_set(gene_sets_db):
    gene_set = gene_sets_db.get_gene_set('main', 'main_candidates')

    assert gene_set is not None
    assert gene_set['name'] == 'main_candidates'
    assert gene_set['count'] == 9
    assert set(gene_set['syms']) == {'POGZ', 'CHD8', 'ANK2', 'FAT4', 'NBEA',
                                     'CELSR1', 'USP7', 'GOLGA5', 'PCSK2'}
    assert gene_set['desc'] == 'Main Candidates'


def test_load_gene_set_from_file(gene_sets_db):
    expected = {
        'POGZ': {'abc-(1)': 1, 'abc-(11)': 1},
        'CHD8': {'abc-(2)': 1},
        'ANK2': {'abc-(3)': 1},
        'FAT4': {'abc-(4)': 1},
        'NBEA': {'abc-(5)': 1},
        'CELSR1': {'abc-(6)': 1, 'abc-(61)': 1, 'abc-(62)': 1, 'abc-(63)': 1},
        'USP7': {'abc-(7)': 1},
        'GOLGA5': {'abc-(8)': 1},
        'PCSK2': {'abc-(9)': 1},
    }

    filepath = path_to_fixtures('geneInfo/sample-map.txt')
    gene_term = GeneSetsDb.load_gene_set_from_file(
        filepath, gene_sets_db.config
    )
    assert isinstance(gene_term, GeneTerms)

    for key, val in gene_term.g2T.items():
        assert key in expected
        for term, count in expected[key].items():
            assert count == expected[key][term]
