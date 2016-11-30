'''
Created on Nov 7, 2016

@author: lubo
'''
from gene.weights import Weights
import pytest


def test_weights_default():
    w = Weights('RVIS_rank')
    df = w.to_df()
    # df = w.load_weights()
    assert df is not None

    assert 'RVIS_rank' in df.columns


# def test_weights_min_max():
#     w = Weights('LGD_rank')
#     # w.load_weights()
#
#     assert 1.0 == w.weights().min()
#     assert 18394.5 == w.weights().max()


def test_weights_get_genes():
    w = Weights('LGD_rank')
    # w.load_weights()

    genes = w.get_genes(1.5, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 5 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 5 == len(genes)


def test_list_gene_weights():
    names = Weights.list_gene_weights()
    assert names is not None

    assert 'LGD_rank' in names
    print(names)


def test_load_gene_weights():
    w = Weights.load_gene_weights("LGD_rank")
    assert w is not None
    assert isinstance(w, Weights)


def test_load_gene_weights_throws():
    with pytest.raises(AssertionError):
        Weights.load_gene_weights("ala bala")
