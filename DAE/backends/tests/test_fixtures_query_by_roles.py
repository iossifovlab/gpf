'''
Created on Jul 2, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import
from __future__ import unicode_literals

import pytest

from RegionOperations import Region

from variants.attributes import Role

from ..attributes_query import role_query


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_impala",
])
@pytest.mark.parametrize("fixture_name,regions,roles,count", [
    ("backends/effects_trio_dad", None, 'dad', 1),
    ("backends/effects_trio", None, 'dad', 1),
    ("backends/trios2", [Region("1", 11539, 11552)], 'prb', 2),
])
def test_fixture_query_by_roles(
        variants_impl, variants, fixture_name, regions, roles, count):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        roles=roles)
    vs = list(vs)
    print(vs)
    assert len(vs) == count


def test_roles_matcher():
    roles = 'dad'

    roles = role_query.transform_tree_to_matcher(
        role_query.transform_query_string_to_tree(roles))
    assert roles.match([Role.dad])
    assert roles.match([Role.dad, Role.mom])
    assert not roles.match([Role.mom])
