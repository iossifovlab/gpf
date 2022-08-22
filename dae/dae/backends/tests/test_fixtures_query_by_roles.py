# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.variants.attributes import Role
from dae.backends.attributes_query import role_query


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "fixture_name,regions,roles,count",
    [
        ("backends/effects_trio_dad", None, "dad", 1),
        ("backends/effects_trio", None, "dad", 1),
        ("backends/trios2", [Region("1", 11539, 11552)], "prb", 2),
    ],
)
def test_fixture_query_by_roles(
    variants_impl, variants, fixture_name, regions, roles, count
):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(regions=regions, roles=roles)
    vs = list(vs)
    print(vs)
    assert len(vs) == count


def test_roles_matcher():
    roles = "dad"

    roles = role_query.transform_tree_to_matcher(
        role_query.transform_query_string_to_tree(roles)
    )
    assert roles.match([Role.dad])
    assert roles.match([Role.dad, Role.mom])
    assert not roles.match([Role.mom])
