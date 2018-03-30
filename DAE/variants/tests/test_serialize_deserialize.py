'''
Created on Mar 30, 2018

@author: lubo
'''
from __future__ import print_function
from variants.loader import RawVariantsLoader
import pytest
from RegionOperations import Region
from variants.tests.common import assert_annotation_equals


# def test_serialize_csv(full_vcf, temp_filename):
#     fvars = full_vcf("fixtures/effects_trio")
#
#     assert fvars.annot_df is not None

@pytest.mark.parametrize("region,worst_effect", [
    (Region('1', 878109, 878109), ("missense", "missense")),
    (Region('1', 901921, 901921), ("synonymous", "missense")),
    (Region('1', 905956, 905956), ("frame-shift", "missense")),
])
def test_serialize_deserialize_worst_effect(
        full_vcf, region, worst_effect, effect_annotator):
    fvars = full_vcf("fixtures/effects_trio_multi")
    vs = fvars.query_variants(regions=[region])
    for v in vs:
        effects1 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position, v.reference, v.alt[1])
        effects2 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position, v.reference, v.alt[2])
        print(effects1, effects2)
        assert worst_effect[0] == effect_annotator.worst_effect(effects1)
        assert worst_effect[1] == effect_annotator.worst_effect(effects2)


@pytest.mark.parametrize("region,worst_effect", [
    (Region('1', 878109, 878109), ("missense", "missense")),
    (Region('1', 901921, 901921), ("synonymous", "missense")),
    (Region('1', 905956, 905956), ("frame-shift", "missense")),
])
def test_serialize_deserialize_gene_effect(
        full_vcf, region, worst_effect, effect_annotator):
    fvars = full_vcf("fixtures/effects_trio_multi")
    vs = fvars.query_variants(regions=[region])
    for v in vs:
        effects1 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position, v.reference, v.alt[1])
        effects2 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position, v.reference, v.alt[2])
        print(effect_annotator.gene_effect(effects1))
        print(effect_annotator.gene_effect(effects2))


@pytest.mark.parametrize("region,worst_effect", [
    (Region('1', 878109, 878109), ("missense", "missense")),
    (Region('1', 901921, 901921), ("synonymous", "missense")),
    (Region('1', 905956, 905956), ("frame-shift", "missense")),
])
def test_serialize_deserialize_transcript_effect(
        full_vcf, region, worst_effect, effect_annotator):
    fvars = full_vcf("fixtures/effects_trio_multi")
    vs = fvars.query_variants(regions=[region])
    for v in vs:
        effects1 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position, v.reference, v.alt[1])
        effects2 = effect_annotator.do_annotate_variant(
            v.chromosome, v.position, v.reference, v.alt[2])
        print(effect_annotator.transcript_effect(effects1))
        print(effect_annotator.transcript_effect(effects2))


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio"
])
def test_serialize_csv(fixture_name, full_vcf, temp_filename):
    fvars = full_vcf(fixture_name)

    assert fvars.annot_df is not None

    outfile = temp_filename
    # outfile = "annot.tmp"

    RawVariantsLoader.save_annotation_file(
        fvars.annot_df, outfile, storage='csv')
    annot_df = RawVariantsLoader.load_annotation_file(
        outfile, storage='csv')
    assert annot_df is not None

    assert_annotation_equals(annot_df, fvars.annot_df)


def test_serialize_csv_vcf19(nvcf19f, temp_filename):
    fvars = nvcf19f

    assert fvars.annot_df is not None

    outfile = temp_filename
    # outfile = "annot.tmp"

    RawVariantsLoader.save_annotation_file(
        fvars.annot_df, outfile, storage='csv')
    annot_df = RawVariantsLoader.load_annotation_file(
        outfile, storage='csv')
    assert annot_df is not None

    assert_annotation_equals(annot_df, fvars.annot_df)
