'''
Created on Jul 1, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

from RegionOperations import Region


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,regions,count", [
    ("fixtures/effects_trio_multi", None, 3),

    ("fixtures/effects_trio_multi", [Region("1", 878109, 878109)], 1),
    ("fixtures/effects_trio_multi", [Region("1", 878109, 901921)], 2),
    ("fixtures/effects_trio_multi", [Region("1", 878109, 905956)], 3),
    ("fixtures/effects_trio_multi",
     [Region("1", 878109, 878109), Region("1", 905956, 905956)], 2),


    ("fixtures/effects_trio", [Region("1", 865582, 865582)], 1),
    ("fixtures/effects_trio", [Region("1", 865582, 1222518)], 10),
    ("fixtures/effects_trio", [Region("1", 865582, 865624)], 3),
    ("fixtures/effects_trio", [Region("1", 878109, 905956)], 3),
    ("fixtures/effects_trio",
     [Region("1", 865582, 865624), Region("1", 878109, 905956)], 6),

    ("fixtures/inheritance_multi", [Region("1", 11500, 11521)], 6),
    ("fixtures/inheritance_multi", [Region("1", 11500, 11501)], 2),
    ("fixtures/inheritance_multi", [Region("1", 11503, 11511)], 2),
    ("fixtures/inheritance_multi",
     [Region("1", 11500, 11501), Region("1", 11503, 11511)], 4),

    ("fixtures/trios2", [Region("1", 11539, 11539)], 2),
    ("fixtures/trios2", [Region("1", 11550, 11550)], 2),
    ("fixtures/trios2",
     [Region("1", 11539, 11539), Region("1", 11550, 11550)], 4),

])
def test_fixture_query_by_regions(
        variants_impl, variants, fixture_name, regions, count):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        return_reference=True,
        return_unknown=True)
    vs = list(vs)
    print(vs)
    assert len(vs) == count
