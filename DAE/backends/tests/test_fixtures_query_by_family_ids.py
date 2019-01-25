'''
Created on Jul 2, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

from RegionOperations import Region


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,regions,family_ids,count", [

    ("fixtures/trios2", [Region("1", 11539, 11539)], ['f1'], 1),
    ("fixtures/trios2", [Region("1", 11539, 11539)], ['f2'], 1),
    ("fixtures/trios2", [Region("1", 11539, 11539)], ['f1', 'f2'], 2),
    ("fixtures/trios2", [Region("1", 11539, 11539)], [], 0),
    ("fixtures/trios2", [Region("1", 11539, 11539)], None, 2),

    ("fixtures/trios2",
     [Region("1", 11539, 11539), Region("1", 11550, 11550)], ['f1'], 2),
    ("fixtures/trios2",
     [Region("1", 11539, 11539), Region("1", 11550, 11550)], ['f2'], 2),
    ("fixtures/trios2",
     [Region("1", 11539, 11539), Region("1", 11550, 11550)], ['f1', 'f2'], 4),
    ("fixtures/trios2",
     [Region("1", 11539, 11539), Region("1", 11550, 11550)], [], 0),
    ("fixtures/trios2",
     [Region("1", 11539, 11539), Region("1", 11550, 11550)], None, 4),
])
def test_fixture_query_by_family_ids(
        variants_impl, variants, fixture_name, regions, family_ids, count):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        family_ids=family_ids,
        return_reference=True,
        return_unknown=True)
    vs = list(vs)
    print(vs)
    assert len(vs) == count
