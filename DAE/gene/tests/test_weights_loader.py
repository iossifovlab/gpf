'''
Created on Nov 7, 2016

@author: lubo
'''
from gene.weights import WeightsLoader


def test_weights_default():
    weights = WeightsLoader()
    assert weights is not None


def test_weights_rvis_rank():
    weights = WeightsLoader()
    assert weights['RVIS_rank'] is not None

    rvis = weights['RVIS_rank']
    assert rvis.df is not None

    assert 'RVIS_rank' in rvis.df.columns


def test_weights_has_rvis_rank():
    weights = WeightsLoader()
    assert 'RVIS_rank' in weights
