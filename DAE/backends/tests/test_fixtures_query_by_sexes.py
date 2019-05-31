'''
Created on Jul 3, 2018

@author: lubo
'''
from __future__ import unicode_literals, print_function, absolute_import

import pytest


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_impala",
])
@pytest.mark.parametrize("fixture_name,sexes,count", [
    ("fixtures/effects_trio_dad", 'male', 1),
    ("fixtures/effects_trio_dad", None, 2),
    ("fixtures/effects_trio_dad", 'female', 1),
    ("fixtures/effects_trio_dad", 'male or female', 2),
    ("fixtures/trios2", 'female', 17),
    ("fixtures/trios2", 'male', 15),
    ("fixtures/trios2", 'female and not male', 9),
    ("fixtures/trios2", 'male and not female', 7),
])
def test_fixture_query_by_sex(
        variants_impl, variants, fixture_name, sexes, count):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        sexes=sexes)
    vs = list(vs)
    for v in vs:
        for a in v.alleles:
            print(
                a, a.inheritance_in_members,
                a.variant_in_members, a.variant_in_sexes)
    assert len(vs) == count
