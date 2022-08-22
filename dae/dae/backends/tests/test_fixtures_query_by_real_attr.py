# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "real_attr_filter,count",
    [
        (None, 20),
        ([("af_allele_count", (0, 0))], 2),
        ([("af_allele_count", (1, 1))], 2),
        ([("af_allele_freq", (100.0 / 8.0, 100.0 / 8.0))], 2),
        ([("af_allele_count", (1, 2))], 14),
        ([("af_allele_freq", (100.0 / 8.0, 200.0 / 8.0))], 14),
        ([("af_allele_count", (2, 2))], 12),
        ([("af_allele_freq", (200.0 / 8.0, 200.0 / 8.0))], 12),
        ([("af_allele_count", (3, 3))], 0),
        ([("af_allele_count", (3, None))], 4),
        ([("af_allele_freq", (300.0 / 8.0, None))], 4),
        ([("af_allele_count", (8, 8))], 4),
        ([("af_allele_freq", (100.0, 100.0))], 4),
    ],
)
def test_variant_real_attr_frequency_queries(
    variants, variants_impl, real_attr_filter, count
):

    fvars = variants_impl(variants)("backends/trios2")
    vs = list(
        fvars.query_variants(
            real_attr_filter=real_attr_filter,
            return_reference=False,
            return_unknown=False,
        )
    )
    assert len(vs) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
def test_variant_ultra_rare_frequency_queries(
    variants, variants_impl,
):

    fvars = variants_impl(variants)("backends/trios2")
    vs = list(
        fvars.query_variants(
            ultra_rare=True, return_reference=False, return_unknown=False
        )
    )
    print(vs)

    assert len(vs) == 4
