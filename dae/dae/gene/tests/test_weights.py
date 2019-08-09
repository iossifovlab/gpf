'''
Created on Nov 7, 2016

@author: lubo
'''
from dae.gene.weights import Weights
import pytest


def test_weights_default(gene_info_config):
    config = gene_info_config.gene_weights.get('RVIS_rank')
    w = Weights(config)
    df = w.to_df()
    # df = w.load_weights()
    assert df is not None

    assert 'RVIS_rank' in df.columns


# def test_weights_min_max(gene_info_config):
#     config = gene_info_config.gene_weights.get('LGD_rank')
#     w = Weights(config)
#     # w.load_weights()
#
#     assert 1.0 == w.weights().min()
#     assert 18394.5 == w.weights().max()


def test_weights_get_genes(gene_info_config):
    config = gene_info_config.gene_weights.get('LGD_rank')
    w = Weights(config)
    # w.load_weights()

    genes = w.get_genes(1.5, 5.0)
    assert 3 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 4 == len(genes)


def test_list_gene_weights(gene_info_config):
    names = Weights.list_gene_weights(gene_info_config.gene_weights)
    assert names is not None

    assert 'LGD_rank' in names


def test_load_gene_weights(gene_info_config):
    w = Weights.load_gene_weights('LGD_rank', gene_info_config.gene_weights)
    assert w is not None
    assert isinstance(w, Weights)


def test_load_gene_weights_throws(gene_info_config):
    with pytest.raises(AssertionError):
        Weights.load_gene_weights('ala bala', gene_info_config.gene_weights)
