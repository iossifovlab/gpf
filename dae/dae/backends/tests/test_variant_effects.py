"""
Created on Mar 27, 2018

@author: lubo
"""
import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize(
    "region,worst_effect",
    [
        (Region("1", 865582, 865582), "synonymous"),
        (Region("1", 865583, 865583), "synonymous"),
        (Region("1", 865624, 865624), "missense"),
        (Region("1", 865627, 865627), "missense"),
        (Region("1", 865664, 865664), "synonymous"),
        (Region("1", 865691, 865691), "missense"),
    ],
)
def test_single_alt_allele_effects(variants_vcf, region, worst_effect):
    fvars = variants_vcf("backends/effects_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == 1
    for v in vs:
        assert len(v.effects) == 1
        assert v.effects[0].worst == worst_effect
        assert v.effects[0].transcripts is not None
        print(v.effects[0].transcripts)


@pytest.mark.parametrize(
    "region,worst_effect",
    [
        (Region("1", 878109, 878109), ("missense", "missense")),
        (Region("1", 901921, 901921), ("synonymous", "missense")),
        (Region("1", 905956, 905956), ("frame-shift", "missense")),
    ],
)
def test_multi_alt_allele_effects(variants_vcf, region, worst_effect):
    fvars = variants_vcf("backends/effects_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == 1
    for v in vs:
        print(v.effects)
        # assert len(v.effects) == 2
        assert v.effects[0].worst == worst_effect[0]
        # assert v.effects[2].worst == worst_effect[1]


@pytest.mark.parametrize(
    "region,worst_effect",
    [
        (Region("1", 878109, 878109), ("missense", "missense")),
        (Region("1", 901921, 901921), ("synonymous", "missense")),
        (Region("1", 905956, 905956), ("frame-shift", "missense")),
    ],
)
def test_multi_alt_allele_effects_match_family(
    variants_vcf, region, worst_effect
):

    fvars = variants_vcf("backends/effects_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == 1

    for v in vs:
        checked = False
        for va in v.alt_alleles:
            checked = True
            assert va.effects.worst == worst_effect[0]
            assert va.effects.transcripts is not None
        assert checked
