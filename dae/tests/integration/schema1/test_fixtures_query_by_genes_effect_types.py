# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,effect,count",
    [
        ([Region("1", 865582, 865691)], "synonymous", 3),
        ([Region("1", 865582, 865691)], "missense", 3),
        ([Region("1", 878109, 905956)], "missense", 1),
        ([Region("1", 878109, 905956)], "synonymous", 1),
        ([Region("1", 878109, 905956)], "frame-shift", 1),
    ],
)
def test_single_alt_allele_effects(
    variants_impl, variants, regions, effect, count
):
    fvars = variants_impl(variants)("backends/effects_trio")
    actual_variants = list(fvars.query_variants(regions=regions,
                                                effect_types=[effect]))
    for v in actual_variants:
        print(v.effects)
    assert len(actual_variants) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
def test_no_missense_effects(variants_impl, variants):
    fvars = variants_impl(variants)("backends/effects_trio_nomissense")
    actual_variants = list(fvars.query_variants(effect_types=["missense"]))
    assert len(actual_variants) == 0


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "effect,count", [("missense", 3), ("frame-shift", 1), ("synonymous", 1)]
)
def test_multi_alt_allele_effects(variants_impl, variants, effect, count):
    fvars = variants_impl(variants)("backends/effects_trio_multi")
    actual_variants = list(fvars.query_variants(effect_types=[effect]))
    for v in actual_variants:
        print(v.effects)
    assert len(actual_variants) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,effects,genes,count",
    [
        (None, None, None, 10),
        (None, None, ["SAMD11"], 7),
        (None, None, ["PLEKHN1"], 2),
        (None, None, ["SCNN1D"], 1),
        (None, ["synonymous"], ["SAMD11"], 3),
        (None, ["missense"], ["SAMD11"], 4),
        (None, ["frame-shift"], ["SAMD11"], 0),
        (None, ["synonymous"], ["PLEKHN1"], 1),
        (None, ["missense", "frame-shift"], ["PLEKHN1"], 1),
        (None, ["synonymous", "frame-shift"], ["PLEKHN1"], 2),
        (
            None,
            ["synonymous", "frame-shift", "3'UTR", "5'UTR"],
            ["PLEKHN1"],
            2,
        ),
    ],
)
def test_single_alt_allele_genes(
    variants_impl, variants, regions, effects, genes, count
):
    fvars = variants_impl(variants)("backends/effects_trio")
    actual_variants = list(
        fvars.query_variants(
            regions=regions, effect_types=effects, genes=genes,
        )
    )
    for v in actual_variants:
        print(v.effects)
    assert len(actual_variants) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,effects,genes,count",
    [(None, None, None, 10), (None, None, [], 0), (None, [], None, 0)],
)
def test_empty_lists(variants_impl, variants, regions, effects, genes, count):
    fvars = variants_impl(variants)("backends/effects_trio")
    actual_variants = list(
        fvars.query_variants(
            regions=regions, effect_types=effects, genes=genes,
        )
    )
    for v in actual_variants:
        print(v.effects)
    assert len(actual_variants) == count
