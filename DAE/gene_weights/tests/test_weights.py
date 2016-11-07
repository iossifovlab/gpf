'''
Created on Nov 7, 2016

@author: lubo
'''
from gene_weights.weights import Weights


def test_weight_base_default():
    w = Weights('RVIS_rank')

    df = w.load_weights()
    assert df is not None

    assert 'RVIS_rank' in df.columns
