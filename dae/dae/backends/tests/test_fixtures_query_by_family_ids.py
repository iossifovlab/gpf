"""
Created on Jul 2, 2018

@author: lubo
"""
import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "fixture_name,regions,family_ids,count",
    [
        ("backends/trios2", [Region("1", 11539, 11539)], ["f1"], 1),
        ("backends/trios2", [Region("1", 11539, 11539)], ["f2"], 1),
        ("backends/trios2", [Region("1", 11539, 11539)], ["f1", "f2"], 2),
        ("backends/trios2", [Region("1", 11539, 11539)], [], 0),
        ("backends/trios2", [Region("1", 11539, 11539)], None, 2),
        (
            "backends/trios2",
            [Region("1", 11539, 11539), Region("1", 11551, 11551)],
            ["f1"],
            2,
        ),
        (
            "backends/trios2",
            [Region("1", 11539, 11539), Region("1", 11551, 11551)],
            ["f2"],
            2,
        ),
        (
            "backends/trios2",
            [Region("1", 11539, 11539), Region("1", 11551, 11551)],
            ["f1", "f2"],
            4,
        ),
        (
            "backends/trios2",
            [Region("1", 11539, 11539), Region("1", 11551, 11551)],
            [],
            0,
        ),
        (
            "backends/trios2",
            [Region("1", 11539, 11539), Region("1", 11551, 11551)],
            None,
            4,
        ),
    ],
)
def test_fixture_query_by_family_ids(
    variants_impl, variants, fixture_name, regions, family_ids, count
):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        family_ids=family_ids,
        return_reference=False,
        return_unknown=False,
    )
    vs = list(vs)
    print(vs)
    assert len(vs) == count
