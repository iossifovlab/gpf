# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import numpy as np

from dae.utils.regions import Region


@pytest.mark.parametrize(
    "region",
    [
        Region("1", 878109, 878109),
        Region("1", 901921, 901921),
        Region("1", 905956, 905956),
    ],
)
def test_multi_alt_allele_genotype(variants_vcf, region):
    fvars = variants_vcf("backends/effects_trio")
    variants = list(fvars.query_variants(regions=[region]))
    assert len(variants) == 1

    for v in variants:
        assert v.gt.shape == (2, 3)
        assert np.all(v.gt[:, 0] == np.array([0, 1]))
        assert np.all(v.gt[:, 2] == np.array([0, 1]))

        assert len(v.genotype) == 3
        assert v.genotype[0] == [0, 1]
        assert v.genotype[1] == [0, 0]
        assert v.genotype[2] == [0, 1]


@pytest.mark.parametrize(
    "region,worst_effect",
    [
        (Region("1", 878109, 878109), ("missense", "missense")),
        (Region("1", 901921, 901921), ("synonymous", "missense")),
        (Region("1", 905956, 905956), ("frame-shift", "missense")),
    ],
)
def test_multi_alt_allele_genotype2(variants_vcf, region, worst_effect):
    fvars = variants_vcf("backends/effects_trio_multi")
    variants = list(fvars.query_variants(regions=[region]))
    assert len(variants) == 1

    for v in variants:
        assert len(v.genotype) == 3
        assert v.genotype[0] == [0, 1]
        assert v.genotype[1] == [0, 2]
        assert v.genotype[2] == [1, 2]


@pytest.mark.parametrize(
    "region,genotype",
    [
        (Region("1", 11500, 11500), np.array([[0, 1], [0, 0], [0, 0]])),
        (Region("1", 11501, 11501), np.array([[0, 2], [0, 0], [0, 0]])),
        (Region("1", 11502, 11502), np.array([[0, 0], [0, 0], [0, 0]])),
        (Region("1", 11503, 11503), np.array([[0, -1], [0, 0], [0, 0]])),
        (Region("1", 11504, 11504), np.array([[0, 1], [0, 2], [0, 0]])),
        (Region("1", 11505, 11505), np.array([[0, 1], [0, 2], [0, 3]])),
    ],
)
def test_trios_multi_alt_allele_genotype2(variants_vcf, region, genotype):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[region], return_reference=True, return_unknown=True
        )
    )
    assert len(variants) == 1

    for v in variants:
        assert len(v.genotype) == 3
        assert v.genotype[0] == list(genotype[0, :])
        assert v.genotype[1] == list(genotype[1, :])
        assert v.genotype[2] == list(genotype[2, :])
