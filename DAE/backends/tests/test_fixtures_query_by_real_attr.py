'''
Created on Jul 5, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest


@pytest.mark.xfail(reason='queries by genomic scores are broken in impala')
@pytest.mark.parametrize("variants", [
    'vcf_import_thift',
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
