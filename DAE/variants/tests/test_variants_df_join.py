'''
Created on Jul 1, 2018

@author: lubo
'''
from __future__ import print_function
import pytest


pytestmark = pytest.mark.xfail


def test_fix_broken_trios2_11602_variants(variants_df):

    dfvars = variants_df("fixtures/trios2_11602")
    assert dfvars is not None

    vs = dfvars.query_variants()
    vs = list(vs)
    for v in vs:
        print(v)
    assert len(vs) == 2
    v0 = vs[0]
    v1 = vs[1]

    assert v0.summary_variant == v1.summary_variant
    sv = v0.summary_variant
    assert sv.alternative == "G,A"
    assert v0.alternative == "A"
    assert v1.alternative is None


def test_fix_broken_trios2_11605_variants(variants_df):

    dfvars = variants_df("fixtures/trios2_11605")
    assert dfvars is not None

    vs = dfvars.query_variants()
    vs = list(vs)
    for v in vs:
        print(v)
    assert len(vs) == 2
    v0 = vs[0]
    v1 = vs[1]

    assert v0.summary_variant == v1.summary_variant
    sv = v0.summary_variant
    assert sv.alternative == "G,A"
    assert v0.alternative == "G,A"
    assert v1.alternative == "G,A"


def test_inspect_broken_trios2_11602_variants(variants_vcf):

    dfvars = variants_vcf("fixtures/trios2_11602")
    assert dfvars is not None

    vs = dfvars.query_variants(
        return_reference=True,
        return_unknown=True)
    vs = list(vs)

    for v in vs:
        print(v)
    assert len(vs) == 2
    v0 = vs[0]
    v1 = vs[1]

    assert v0.summary_variant == v1.summary_variant
    sv = v0.summary_variant
    assert sv.alternative == "G,A"
    assert v0.alternative == "A"
    assert v1.alternative is None
