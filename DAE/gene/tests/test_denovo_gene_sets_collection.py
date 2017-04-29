'''
Created on Feb 16, 2017

@author: lubo
'''
import pytest
from gene.gene_set_collections import GeneSetsCollections


@pytest.fixture(scope='session')
def gscs(request):
    res = GeneSetsCollections()
    return res


def test_denovo_gene_sets_types(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    assert denovo is not None
    assert denovo.gene_sets_types == \
        [
            'autism',
            'congenital heart disease',
            'epilepsy',
            'intellectual disability',
            'schizophrenia',
            'unaffected'
        ]


def test_denovo_get_gene_set_lgds_autism(gscs):
    lgds = gscs.get_gene_set('denovo', 'LGDs', ['autism'])
    assert lgds is not None
    assert lgds['count'] == 546
    assert lgds['name'] == 'LGDs'


def test_denovo_get_gene_set_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set('denovo', 'LGDs', ['autism', 'epilepsy'])
    assert lgds is not None
    assert lgds['count'] == 576
    assert lgds['name'] == 'LGDs'


def test_denovo_get_gene_sets_autism(gscs):
    gene_sets = gscs.get_gene_sets('denovo', ['autism'])
    assert gene_sets is not None
    assert len(gene_sets) == 16
    gs = gene_sets[0]
    assert gs['count'] == 546
    assert gs['name'] == 'LGDs'


def test_denovo_get_gene_sets_autism_and_epilepsy(gscs):
    gene_sets = gscs.get_gene_sets(
        'denovo',
        gene_sets_types=['autism', 'epilepsy'])
    assert gene_sets is not None
    assert len(gene_sets) == 16
    gs = gene_sets[0]
    assert gs['count'] == 576
    assert gs['name'] == 'LGDs'


def test_denovo_low_iq(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set('LGDs.LowIQ', gene_sets_types=['autism'])
    assert gs is not None
    assert gs['count'] == 219


def test_denovo_high_iq(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set('LGDs.HighIQ', gene_sets_types=['autism'])
    assert gs is not None
    assert gs['count'] == 168


def test_denovo_lgds_recurrent(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    gs = denovo.get_gene_set('LGDs.Recurrent', gene_sets_types=['autism'])
    assert gs is not None
    assert gs['count'] == 45
