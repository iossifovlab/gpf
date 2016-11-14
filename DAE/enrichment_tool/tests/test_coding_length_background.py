'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np

from enrichment_tool.background import CodingLenBackground
import pytest
from DAE import get_gene_sets_symNS


def test_coding_length_background_default():
    background = CodingLenBackground()

    assert background.background is not None

    background.cache_save()

    b1 = CodingLenBackground()
    assert b1.cache_load()
    assert b1.background is not None

    assert np.all(background.background == b1.background)


@pytest.fixture(scope='module')
def background(request):
    bg = CodingLenBackground()
    return bg


@pytest.fixture(scope='module')
def gene_syms(request):
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['FMRP Tuschl'].keys()
    return gene_set


def test_load(background):
    background = CodingLenBackground()
    bg = background._load_and_prepare_build()
    assert bg is not None


def test_max_sym_len(background):
    background = CodingLenBackground()
    bg = background._load_and_prepare_build()

    max_sym_len = max([len(s) for (s, _l) in bg])
    assert max_sym_len < 32


def test_precompute(background):
    background = CodingLenBackground()
    bg = background.precompute()
    assert bg is not None

    assert background.is_ready


def test_total(background):
    background = CodingLenBackground()
    background.precompute()
    assert 33100101 == background._total


def test_count(background, gene_syms):
    background = CodingLenBackground()
    background.precompute()
    assert 3395921, background._count(gene_syms)


def test_prob(background, gene_syms):
    background = CodingLenBackground()
    background.precompute()
    assert 0.10259 == pytest.approx(background._prob(gene_syms), 4)


def test_serialize_deserialize(background):
    background = CodingLenBackground()
    background.precompute()

    data = background.serialize()

    b2 = CodingLenBackground()
    b2.deserialize(data)

    np.testing.assert_array_equal(background.background, b2.background)
