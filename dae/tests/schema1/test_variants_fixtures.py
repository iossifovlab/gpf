# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "fixture_name,count",
    [
        ("backends/effects_trio_multi", 3),
        ("backends/effects_trio", 10),
        # ("backends/inheritance_multi", 6),
        # ("fixtures/trios2", 30),
    ],
)
def test_variants_all_count(variants_impl, variants, fixture_name, count):

    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    actual_variants = vvars.query_variants(return_reference=True,
                                           return_unknown=True)
    actual_variants = list(actual_variants)
    print(actual_variants)
    assert len(actual_variants) == count


@pytest.mark.parametrize("fixture_name", ["backends/trios2"])
@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
def test_df_query_multiallelic3_families(
    variants_impl, variants, fixture_name
):

    dfvars = variants_impl(variants)(fixture_name)
    assert dfvars is not None

    regions = [Region("1", 11606, 11606)]
    family_ids = ["f1"]
    actual_variants = dfvars.query_variants(
        regions=regions,
        family_ids=family_ids,
        return_reference=True,
        return_unknown=True,
    )
    actual_variants = list(actual_variants)
    assert len(actual_variants) == 1
    v = actual_variants[0]

    print(v, mat2str(v.best_state))
    fa1 = v.alt_alleles[0]
    fa2 = v.alt_alleles[1]
    assert len(v.alt_alleles) == 2

    assert "mom1" in fa1.variant_in_members
    assert "dad1" in fa2.variant_in_members
    assert "ch1" not in fa1.variant_in_members
    assert "ch1" not in fa2.variant_in_members


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize("fixture_name", ["backends/trios2_11541"])
def test_reference_variant(variants_impl, variants, fixture_name):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    actual_variants = fvars.query_variants(return_reference=True,
                                           return_unknown=True)
    actual_variants = list(actual_variants)
    assert len(actual_variants) == 2
    print(actual_variants)

    for v in actual_variants:
        print(v.family_id, mat2str(v.best_state))

    # assert vs[0].summary_variant == vs[1].summary_variant


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize("fixture_name", ["backends/trios2_11600"])
def test_reference_multiallelic_variant(variants_impl, variants, fixture_name):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    actual_variants = fvars.query_variants(return_reference=True,
                                           return_unknown=True)
    actual_variants = list(actual_variants)
    print(actual_variants)
    assert len(actual_variants) == 2

    for v in actual_variants:
        print(mat2str(v.best_state))

    # assert vs[0].summary_variant == vs[1].summary_variant


@pytest.mark.parametrize("fixture_name", ["backends/strange_01"])
@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
def test_query_strange_multiallelic_families(
    variants_impl, variants, fixture_name
):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    actual_variants = fvars.query_variants()
    actual_variants = list(actual_variants)
    assert len(actual_variants) == 2
    for v in actual_variants:
        # v = vs[0]

        print(v, mat2str(v.best_state))
        print(v.alt_alleles)

        fa1 = v.alt_alleles[0]
        fa2 = v.alt_alleles[1]
        assert len(v.alt_alleles) == 2

        print(fa1.variant_in_members)
        print(fa2.variant_in_members)

        # assert "mom1" in fa1.variant_in_members
        # assert "dad1" in fa2.variant_in_members
        # assert "ch1" not in fa1.variant_in_members
        # assert "ch1" not in fa2.variant_in_members
