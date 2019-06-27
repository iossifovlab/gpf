'''
Created on Jul 5, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest


@pytest.mark.xfail(reason='queries by genomic scores are broken in impala')
@pytest.mark.parametrize("variants", [
    # 'vcf_import_thift',
    'vcf_import_raw',
])
@pytest.mark.parametrize("real_attr_filter,count", [
    ([('score0', (None, 865664))], 5),
    ([('score0', (865583, 865664))], 4),
    ([('score0', (865583, 865664)), ('score2', (8656.25, 9019))], 2),
    (None, 10),
    ([], 10),
])
def test_single_alt_allele_variant_types(
        variants, fixture_select,
        real_attr_filter, count):

    fvars = fixture_select(variants)

    vs = fvars.query_variants(
        real_attr_filter=real_attr_filter)
    vs = list(vs)
    for v in vs:
        print(v)
    assert len(vs) == count


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_impala",
])
@pytest.mark.parametrize("real_attr_filter,count", [
    (None, 20),
    ([('af_allele_count', (0, 0))], 2),
    ([('af_allele_count', (1, 1))], 2),
    ([('af_allele_freq', (100.0/8.0, 100.0/8.0))], 2),
    ([('af_allele_count', (1, 2))], 14),
    ([('af_allele_freq', (100.0/8.0, 200.0/8.0))], 14),

    ([('af_allele_count', (2, 2))], 12),
    ([('af_allele_freq', (200.0/8.0, 200.0/8.0))], 12),

    ([('af_allele_count', (3, 3))], 0),

    ([('af_allele_count', (3, None))], 4),
    ([('af_allele_freq', (300.0/8.0, None))], 4),

    ([('af_allele_count', (8, 8))], 4),
    ([('af_allele_freq', (100.0, 100.0))], 4),
])
def test_variant_real_attr_frequency_queries(
        variants, variants_impl, real_attr_filter, count):

    fvars = variants_impl(variants)("backends/trios2")
    vs = list(fvars.query_variants(
        real_attr_filter=real_attr_filter,
        return_reference=False,
        return_unknown=False))
    assert len(vs) == count
    # for v in vs:
    #     print(v)
    #     for a in v.alleles:
    #         print(
    #             "\t>", a,
    #             "\taf_allele_count:", a.get_attribute("af_allele_count"),
    #             "\taf_allele_freq:", a.get_attribute("af_allele_freq"))


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_impala",
])
def test_variant_ultra_rare_frequency_queries(
        variants, variants_impl, ):

    fvars = variants_impl(variants)("backends/trios2")
    vs = list(fvars.query_variants(
        ultra_rare=True,
        return_reference=False,
        return_unknown=False))
    assert len(vs) == 2
