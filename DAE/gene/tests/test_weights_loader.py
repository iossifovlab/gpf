'''
Created on Nov 7, 2016

@author: lubo
'''
from __future__ import unicode_literals


def test_weights_default(weights_loader):
    assert weights_loader is not None


def test_weights_rvis_rank(weights_loader):
    assert weights_loader['RVIS_rank'] is not None

    rvis = weights_loader['RVIS_rank']
    assert rvis.df is not None

    assert 'RVIS_rank' in rvis.df.columns


def test_weights_has_rvis_rank(weights_loader):
    assert 'RVIS_rank' in weights_loader
