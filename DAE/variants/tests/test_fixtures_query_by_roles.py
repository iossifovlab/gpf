'''
Created on Jul 2, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from RegionOperations import Region
from variants.attributes_query import role_query
from variants.attributes import Role


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,regions,roles,count", [
    ("fixtures/effects_trio_dad", None, 'dad', 1),
    ("fixtures/effects_trio", None, 'dad', 1),
    ("fixtures/trios2", [Region("1", 11539, 11552)], 'prb', 2),
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


@pytest.mark.skip("raw_df needs fixing")
@pytest.mark.parametrize("fixture_name,regions,roles,count", [
    ("fixtures/effects_trio_dad", None, 'dad', 1),
])
def test_fixture_query_raw_df_by_roles(
        variants_df, fixture_name, regions, roles, count):
    vvars = variants_df(fixture_name)
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
