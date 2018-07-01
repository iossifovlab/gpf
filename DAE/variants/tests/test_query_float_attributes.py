'''
Created on Mar 8, 2018

@author: lubo
'''
from __future__ import print_function
import numpy as np

from RegionOperations import Region
from variants.raw_vcf import RawFamilyVariants
from variants.vcf_utils import mat2str
import pytest


# def test_alt_all_freq(ustudy_full):
#     regions = [Region("1", 10000, 15000)]
#     vs = ustudy_full.query_variants(regions=regions)
# 
#     for v in vs:
#         assert 'af_alternative_allele_count' in v
#         assert 'af_alternative_allele_freq' in v
#         assert 'af_parents_called_count' in v
#         assert 'af_parents_called_percent' in v


# def test_filter_real_attr(fv_one):
#     v = fv_one
#     v.update_attributes({"a": [1], "b": np.array([2])})
#
#     assert RawFamilyVariants.filter_real_attr(
#         v, {'a': [(1, 2), (3, 4)]})
#
#     assert RawFamilyVariants.filter_real_attr(
#         v, {'a': [[1, 2], [3, 4]]})
#
#     assert not RawFamilyVariants.filter_real_attr(
#         v, {'a': [[1.1, 2], [3, 4]]})
#
#     assert RawFamilyVariants.filter_real_attr(
#         v, {'b': [[1, 2], [3, 4]]})
