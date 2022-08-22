# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize("variants", [
    "variants_impala",
    "variants_vcf",
])
@pytest.mark.parametrize(
    "region,count,freq0,freq1",
    [
        (Region("1", 11539, 11539), 2, 75.0, 25.0),
        (Region("1", 11540, 11540), 2, 75.0, 25.0),
        (Region("1", 11541, 11541), 1, 87.5, 12.5),
        (Region("1", 11542, 11542), 1, 87.5, 12.5),
        (Region("1", 11550, 11550), 0, 100.0, 0.0),
        (Region("1", 11553, 11553), 2, 100.0, 0.0),
        (Region("1", 11551, 11551), 2, 0.0, 100.0),
        (Region("1", 11552, 11552), 2, 0.0, 100.0),
    ],
)
def test_variant_frequency_single(
    variants_impl, variants, region, count, freq0, freq1
):

    fvars = variants_impl(variants)("backends/trios2")
    vs = list(
        fvars.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_state))
        print(v.frequencies)

        assert freq0 == pytest.approx(v.frequencies[0], 1e-2)
        if len(v.frequencies) == 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2)


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "region,count,freq0,freq1,freq2",
    [
        (Region("1", 11600, 11600), 0, 100.0, 0.0, 0.0),
        (Region("1", 11601, 11601), 1, 75.0, 25.0, 0.0),
        (Region("1", 11604, 11604), 1, 75.0, 25.0, 0.0),
        (Region("1", 11602, 11602), 1, 75.0, 0.0, 25.0),
        (Region("1", 11605, 11605), 2, 50.0, 25.0, 25.0),
        (Region("1", 11603, 11603), 1, 75.0, 0.0, 25.0),
    ],
)
def test_variant_frequency_multi_alleles(
    variants, variants_impl, region, count, freq0, freq1, freq2
):

    fvars = variants_impl(variants)("backends/trios2")
    vs = list(
        fvars.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_state))
        print(v.frequencies)
        # assert len(v.frequencies) == 3

        assert freq0 == pytest.approx(v.frequencies[0], 1e-2)
        if len(v.frequencies) == 2:
            assert freq1 == pytest.approx(
                v.frequencies[1], 1e-2
            ) or freq2 == pytest.approx(v.frequencies[1], 1e-2)
        elif len(v.frequencies) > 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2)
            assert freq2 == pytest.approx(v.frequencies[2], 1e-2)


@pytest.mark.parametrize("variants", [
    "variants_impala",
    "variants_vcf"
])
@pytest.mark.parametrize(
    "region,count,freq0,freq1",
    [
        (Region("1", 865582, 865582), 5, 50.0, 50.0),
        (Region("1", 865583, 865583), 5, 50.0, 50.0),
        (Region("1", 865624, 865624), 5, 75.0, 25.0),
        (Region("1", 865627, 865627), 5, 60.0, 40.0),
        (Region("1", 865664, 865664), 5, 75.0, 25.0),
        (Region("1", 865691, 865691), 5, 35.0, 65.0),
    ],
)
def test_variant_frequency_multivcf(
        variants, variants_impl, region, count, freq0, freq1):

    fvars = variants_impl(variants)("backends/multivcf_original")
    vs = list(
        fvars.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_state))
        print(v.frequencies)
        assert len(v.frequencies) == 2

        assert freq0 == pytest.approx(v.frequencies[0], 1e-2)
        if len(v.frequencies) == 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2)


@pytest.mark.parametrize("variants", [
    "variants_impala",
    "variants_vcf"
])
@pytest.mark.parametrize(
    "region,count,freq0,freq1",
    [
        (Region("1", 865582, 865582), 5, 50.0, 50.0),
        (Region("1", 865624, 865624), 2, 50.0, 50.0),
        (Region("1", 865627, 865627), 5, 70.0, 30.0),
        (Region("1", 865664, 865664), 5, 65.0, 35.0),
        (Region("1", 865691, 865691), 5, 55.0, 45.0),
    ],
)
def test_variant_frequency_multivcf_unknown(
        variants, variants_impl, region, count, freq0, freq1):

    fvars = variants_impl(variants)("backends/multivcf_unknown")
    vs = list(
        fvars.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_state))
        print(v.frequencies)
        assert len(v.frequencies) == 2

        assert freq0 == pytest.approx(v.frequencies[0], 1e-2)
        if len(v.frequencies) == 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2)
