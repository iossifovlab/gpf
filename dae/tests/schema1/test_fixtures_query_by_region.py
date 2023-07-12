# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "fixture_name,regions,count",
    [
        ("backends/effects_trio_multi", None, 3),
        ("backends/effects_trio_multi", [Region("1", 878109, 878109)], 1),
        ("backends/effects_trio_multi", [Region("1", 878109, 901921)], 2),
        ("backends/effects_trio_multi", [Region("1", 878109, 905956)], 3),
        (
            "backends/effects_trio_multi",
            [Region("1", 878109, 878109), Region("1", 905956, 905956)],
            2,
        ),
        ("backends/effects_trio", [Region("1", 865582, 865582)], 1),
        ("backends/effects_trio", [Region("1", 865582, 1222518)], 10),
        ("backends/effects_trio", [Region("1", 865582, 865624)], 3),
        ("backends/effects_trio", [Region("1", 878109, 905956)], 3),
        (
            "backends/effects_trio",
            [Region("1", 865582, 865624), Region("1", 878109, 905956)],
            6,
        ),
        # ("backends/inheritance_multi", [Region("1", 11500, 11521)], 5),
        # ("backends/inheritance_multi", [Region("1", 11500, 11501)], 1),
        # ("backends/inheritance_multi", [Region("1", 11503, 11511)], 2),
        # (
        #     "backends/inheritance_multi",
        #     [Region("1", 11500, 11501), Region("1", 11503, 11511)],
        #     3,
        # ),
        ("backends/trios2", [Region("1", 11539, 11539)], 2),
        ("backends/trios2", [Region("1", 11551, 11551)], 2),
        (
            "backends/trios2",
            [Region("1", 11539, 11539), Region("1", 11551, 11551)],
            4,
        ),
    ],
)
def test_fixture_query_by_regions(
    variants_impl, variants, fixture_name, regions, count
):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions, return_reference=False, return_unknown=False
    )
    vs = list(vs)
    print(vs)
    assert len(vs) == count
