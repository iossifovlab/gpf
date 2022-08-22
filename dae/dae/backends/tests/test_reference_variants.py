# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize("fixture_name", ["backends/trios2_11541",])
def test_reference_variant_single_allele(
    variants_impl, variants, fixture_name
):

    dfvars = variants_impl(variants)(fixture_name)
    assert dfvars is not None

    vs = dfvars.query_variants(
        family_ids=["f1"], return_reference=True, return_unknown=True
    )
    vs = list(vs)
    assert len(vs) == 1

    v = vs[0]
    print(v)

    print("best_st:", mat2str(v.best_state))
    print("freq:   ", v.frequencies)
    print("effects:", v.effects)
    print("alleles:", v.alleles)
    # print("summary:", v.summary_variant)

    assert len(v.frequencies) == 1
    assert v.frequencies[0] == pytest.approx(87.5)
    assert not v.effects

    # sv = v.summary_variant

    # print(sv.frequencies)
    # assert len(sv.frequencies) == 2
    # assert sv.frequencies[0] == pytest.approx(87.5)
    # assert sv.frequencies[1] == pytest.approx(12.5)

    # print(sv.effects)
    # assert len(sv.effects) == 1


@pytest.mark.parametrize(
    "variants",
    [
        # 'variants_impala',
        "variants_vcf"
    ],
)
@pytest.mark.parametrize("fixture_name", ["backends/trios2_11541",])
def test_full_variants_iterator(variants_impl, variants, fixture_name):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    full_iterator = fvars.full_variants_iterator()
    for sv, fvs in full_iterator:
        print(sv)
        for fv in fvs:
            print(fv)
