'''
Created on Feb 27, 2017

@author: lubo
'''
from __future__ import unicode_literals
import pytest

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


def name_in_gene_sets(gene_sets, name):
    for gene_set in gene_sets:
        if gene_set['name'] == name:
            return True

    return False


def test_generate_cache(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    computed = denovo.load()
    assert computed is not None


def test_load_cache(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    denovo.load()
    loaded = denovo.load()
    assert loaded is not None


def test_f1_autism_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(gene_sets_types={'f1_group': ['autism']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Synonymous')
    assert name_in_gene_sets(gene_sets, 'Synonymous.WE')


def test_f1_unaffected_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(
        gene_sets_types={'f1_group': ['unaffected']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Missense')
    assert name_in_gene_sets(gene_sets, 'Missense.Male')


def test_f1_single_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(
        gene_sets_types={'f1_group': ['unaffected']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Missense.Single')


def test_synonymous_recurrency_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(
        gene_sets_types={'f2_group': ['autism']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Synonymous.WE.Recurrent')
    assert not name_in_gene_sets(gene_sets, 'Synonymous.WE.Triple')


def test_missense_recurrency_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(
        gene_sets_types={'f2_group': ['unaffected']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Missense.Recurrent')
    assert not name_in_gene_sets(gene_sets, 'Missense.Triple')


def test_synonymous_triple_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(gene_sets_types={'f3_group': ['autism']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Synonymous.WE.Recurrent')
    assert name_in_gene_sets(gene_sets, 'Synonymous.WE.Triple')


def test_missense_triple_get_gene_sets(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')

    gene_sets = denovo.get_gene_sets(
        gene_sets_types={'f3_group': ['unaffected']})

    assert gene_sets

    print("gene_sets", gene_sets)

    assert name_in_gene_sets(gene_sets, 'Missense.Recurrent')
    assert name_in_gene_sets(gene_sets, 'Missense.Triple')
