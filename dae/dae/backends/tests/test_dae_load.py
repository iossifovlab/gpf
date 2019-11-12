'''
Created on Jul 23, 2018

@author: lubo
'''
import numpy as np
from dae.utils.vcf_utils import str2mat, best2gt, GENOTYPE_TYPE, mat2str

from ..dae.raw_dae import RawDAE, BaseDAE


def test_explode_family_genotype():
    fgt = RawDAE._explode_family_genotypes(
        'f3:2121/0101:11 27 34 13/0 26 0 15/0 0 0 0')
    print(fgt)


def test_str2mat():
    res = str2mat("2121/0101")
    assert res.dtype == GENOTYPE_TYPE
    assert np.all(res == np.array([[2, 1, 2, 1], [0, 1, 0, 1]], dtype=np.int8))


def test_best2gt():
    best = np.array([[2, 1, 2, 1], [0, 1, 0, 1]], dtype=np.int8)
    res = best2gt(best)
    assert np.all(res == np.array([[0, 1, 0, 1], [0, 0, 0, 0]], dtype=np.int8))

    best = np.array([[0, 1, 0, 1], [2, 1, 2, 1]], dtype=np.int8)
    res = best2gt(best)
    assert np.all(res == np.array([[1, 1, 1, 1], [1, 0, 1, 0]], dtype=np.int8))


def test_load_denovo(raw_denovo):
    denovo = raw_denovo("backends/denovo")

    assert denovo is not None
    assert denovo.families is not None

    vs = denovo.full_variants_iterator()
    for sv, fvs in vs:
        for v in fvs:
            print(v, mat2str(v.best_st))


def test_load_denovo_families(raw_denovo):
    denovo = raw_denovo("backends/denovo")
    assert denovo.families is not None
