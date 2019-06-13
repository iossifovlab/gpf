'''
Created on Feb 27, 2017

@author: lubo
'''
from __future__ import unicode_literals
import pytest

from gene.denovo_gene_sets_collection import DenovoGeneSetsCollection

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


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


def test_generate_cache(denovo_gene_sets):
    computed = denovo_gene_sets[0].load()
    assert computed is not None


def test_load_cache(denovo_gene_sets):
    denovo_gene_sets[0].load()
    loaded = denovo_gene_sets[0].load()
    assert loaded is not None


def test_f1_autism_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f1_group': {'phenotype': ['autism']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Synonymous', 1)


def test_f1_affected_and_unaffected_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f1_group': {'phenotype': ['autism', 'unaffected']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Synonymous', 1)


def test_f1_unaffected_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f1_group': {'phenotype': ['unaffected']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Missense', 2)
    assert name_in_gene_sets(gene_sets, 'Missense.Male', 2)
    # assert name_in_gene_sets(gene_sets, 'Missense.Female', 0)


def test_f1_single_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f1_group': {'phenotype': ['unaffected']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Missense.Single', 2)
    assert name_in_gene_sets(gene_sets, 'Missense.Male', 2)


def test_synonymous_recurrency_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f2_group': {'phenotype': ['autism']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Synonymous.WE.Recurrent', 1)
    assert not name_in_gene_sets(gene_sets, 'Synonymous.WE.Triple')


def test_missense_recurrency_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f2_group': {'phenotype': ['unaffected']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Missense.Recurrent', 2)
    assert not name_in_gene_sets(gene_sets, 'Missense.Triple')


def test_synonymous_triple_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f3_group': {'phenotype': ['autism']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Synonymous.WE.Recurrent', 1)
    assert name_in_gene_sets(gene_sets, 'Synonymous.WE.Triple', 1)


def test_missense_triple_get_gene_sets(denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f3_group': {'phenotype': ['unaffected']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Missense.Recurrent', 2)
    assert name_in_gene_sets(gene_sets, 'Missense.Triple', 2)


def test_missense_triple_get_gene_sets_affected_and_unaffected(
        denovo_gene_sets):
    gene_sets = DenovoGeneSetsCollection.get_gene_sets(
        denovo_gene_sets,
        gene_sets_types={'f3_group': {'phenotype': ['autism', 'unaffected']}})

    assert gene_sets

    assert name_in_gene_sets(gene_sets, 'Missense.Recurrent', 2)
    assert name_in_gene_sets(gene_sets, 'Missense.Triple', 2)
