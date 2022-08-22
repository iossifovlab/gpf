# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "fixture_name,sexes,count",
    [
        ("backends/effects_trio_dad", "male", 1),
        ("backends/effects_trio_dad", None, 2),
        ("backends/effects_trio_dad", "female", 1),
        ("backends/effects_trio_dad", "male or female", 2),
        ("backends/trios2", "female", 17),
        ("backends/trios2", "male", 15),
        ("backends/trios2", "female and not male", 9),
        ("backends/trios2", "male and not female", 7),
    ],
)
def test_fixture_query_by_sex(
    variants_impl, variants, fixture_name, sexes, count
):
    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(sexes=sexes)
    vs = list(vs)
    for v in vs:
        for a in v.alleles:
            print(
                a,
                a.inheritance_in_members,
                a.variant_in_members,
                a.variant_in_sexes,
            )
    assert len(vs) == count
