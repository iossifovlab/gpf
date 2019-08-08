'''
Created on Mar 30, 2018

@author: lubo
'''
import pytest

from dae.RegionOperations import Region


@pytest.mark.skip
@pytest.mark.parametrize("region,worst_effect", [
    (Region('1', 878109, 878109), ("missense", "missense")),
    (Region('1', 901921, 901921), ("synonymous", "missense")),
    (Region('1', 905956, 905956), ("frame-shift", "missense")),
])
def test_serialize_deserialize_worst_effect(
        variants_vcf, region, worst_effect, effect_annotator):
    fvars = variants_vcf("fixtures/effects_trio_multi")
    vs = fvars.query_variants(regions=[region])
    for v in vs:
        print(v, v.alternative)
        effects1 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position,
            v.reference, v.alt_alleles[0].alternative)
        effects2 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position,
            v.reference, v.alt_alleles[1].alternative)
        print(effects1, effects2)
        assert worst_effect[0] == effect_annotator.worst_effect(effects1)
        assert worst_effect[1] == effect_annotator.worst_effect(effects2)


@pytest.mark.skip
@pytest.mark.parametrize("region,worst_effect", [
    (Region('1', 878109, 878109), ("missense", "missense")),
    (Region('1', 901921, 901921), ("synonymous", "missense")),
    (Region('1', 905956, 905956), ("frame-shift", "missense")),
])
def test_serialize_deserialize_gene_effect(
        variants_vcf, region, worst_effect, effect_annotator):
    fvars = variants_vcf("fixtures/effects_trio_multi")
    vs = fvars.query_variants(regions=[region])
    for v in vs:
        print(v)
        effects1 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position,
            v.reference, v.alt_alleles[0].alternative)
        effects2 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position,
            v.reference, v.alt_alleles[1].alternative)
        print(effect_annotator.gene_effect(effects1))
        print(effect_annotator.gene_effect(effects2))
        assert worst_effect[0] == effect_annotator.worst_effect(effects1)
        assert worst_effect[1] == effect_annotator.worst_effect(effects2)


@pytest.mark.skip
@pytest.mark.parametrize("region,worst_effect", [
    (Region('1', 878109, 878109), ("missense", "missense")),
    (Region('1', 901921, 901921), ("synonymous", "missense")),
    (Region('1', 905956, 905956), ("frame-shift", "missense")),
])
def test_serialize_deserialize_transcript_effect(
        variants_vcf, region, worst_effect, effect_annotator):
    fvars = variants_vcf("fixtures/effects_trio_multi")
    vs = fvars.query_variants(regions=[region])
    for v in vs:
        effects1 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position,
            v.reference, v.alt_alleles[0].alternative)
        effects2 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position,
            v.reference, v.alt_alleles[1].alternative)
        print(effect_annotator.transcript_effect(effects1))
        print(effect_annotator.transcript_effect(effects2))
        assert worst_effect[0] == effect_annotator.worst_effect(effects1)
        assert worst_effect[1] == effect_annotator.worst_effect(effects2)
