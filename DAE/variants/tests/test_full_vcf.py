'''
Created on Mar 16, 2018

@author: lubo
'''
from __future__ import print_function
from variants.vcf_utils import mat2str
import pytest


@pytest.mark.slow
def test_open_raw_vcf_with_region(vcf19r):
    region = "7:121000000-121010000"
    fvars = vcf19r(region)
    assert fvars is not None

    vs = fvars.query_variants(
        inheritance='mendelian')
    for c, v in enumerate(vs):
        print(c, v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene, v.variant_type,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'))
        assert v.get_attr('all.nAltAlls') > 0

        assert v.n_alt_alls is not None
        assert v.alt_alls_freq is not None
        assert v.n_par_called is not None
        assert v.prcnt_par_called is not None


@pytest.mark.slow
def test_raw_vcf_bad_frequency(vcf19r):
    fvars = vcf19r("1:897008-897010")
    vs = fvars.query_variants(
        effect_types=['frame-shift', 'nonsense', 'splice-site'])
    for c, v in enumerate(vs):
        print(c, v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'))
        print(v.members_in_order)
        print(v.variant_in_roles)
        print(v.variant_in_members)

        assert v.get_attr('all.nAltAlls') > 0

        assert v.n_alt_alls is not None
        assert v.alt_alls_freq is not None
        assert v.n_par_called is not None
        assert v.prcnt_par_called is not None
