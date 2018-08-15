'''
Created on Feb 6, 2017

@author: lubo
'''
from __future__ import unicode_literals
import copy
from datasets.tests.requests import EXAMPLE_QUERY_SSC


def test_variant_types_sub(ssc):
    data = copy.deepcopy(EXAMPLE_QUERY_SSC)
    data['variantTypes'] = ['sub']

    vs = ssc.get_denovo_variants(**data)

    for v in vs:
        assert 'sub' in v.variant


def test_variant_types_del(ssc):
    data = copy.deepcopy(EXAMPLE_QUERY_SSC)
    data['variantTypes'] = ['del']

    vs = ssc.get_denovo_variants(**data)

    for v in vs:
        assert 'del' in v.variant


def test_variant_types_sub_del(ssc):
    data = copy.deepcopy(EXAMPLE_QUERY_SSC)
    data['variantTypes'] = ['del', 'sub']

    vs = ssc.get_denovo_variants(**data)

    for v in vs:
        assert 'del' in v.variant or 'sub' in v.variant


def test_child_gender_male(ssc):
    data = copy.deepcopy(EXAMPLE_QUERY_SSC)
    data['gender'] = ['male']

    vs = ssc.get_denovo_variants(**data)

    for v in vs:
        assert 'M' in v.inChS


def test_child_gender_female(ssc):
    data = copy.deepcopy(EXAMPLE_QUERY_SSC)
    data['gender'] = ['female']

    vs = ssc.get_denovo_variants(**data)

    for v in vs:
        assert 'F' in v.inChS
