'''
Created on Nov 7, 2016

@author: lubo
'''
from dae.gene.weights import Weights
import pytest


def test_weights_default(gene_info_config):
    w = Weights('RVIS_rank', config=gene_info_config)
    df = w.to_df()
    # df = w.load_weights()
    assert df is not None

    assert 'RVIS_rank' in df.columns


# def test_weights_min_max(gene_info_config):
#     w = Weights('LGD_rank', config=gene_info_config)
#     # w.load_weights()
#
#     assert 1.0 == w.weights().min()
#     assert 18394.5 == w.weights().max()


def test_weights_get_genes(gene_info_config):
    w = Weights('LGD_rank', config=gene_info_config)
    # w.load_weights()

    genes = w.get_genes(1.5, 5.0)
    assert 3 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 4 == len(genes)


def test_list_gene_weights(gene_info_config):
    names = Weights.list_gene_weights(config=gene_info_config)
    assert names is not None

    assert 'LGD_rank' in names


def test_load_gene_weights(gene_info_config):
    w = Weights.load_gene_weights('LGD_rank', config=gene_info_config)
    assert w is not None
    assert isinstance(w, Weights)


def test_load_gene_weights_throws(gene_info_config):
    with pytest.raises(AssertionError):
        Weights.load_gene_weights('ala bala', config=gene_info_config)
