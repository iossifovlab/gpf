'''
Created on Nov 7, 2016

@author: lubo
'''
from gene_weights.weights import Weights


def test_weights_default():
    w = Weights('RVIS_rank')

    df = w.load_weights()
    assert df is not None

    assert 'RVIS_rank' in df.columns


def test_weights_min_max():
    w = Weights('LGD_rank')
    w.load_weights()

    assert 1.0 == w.weights().min()
    assert 18394.5 == w.weights().max()


def test_weights_get_genes():
    w = Weights('LGD_rank')
    w.load_weights()

    genes = w.get_genes(1.5, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 5 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 5 == len(genes)
