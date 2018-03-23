'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function
# from icecream import ic

import pytest

from variants.loader import RawVariantsLoader
from variants.tests.common import assert_annotation_equals
from variants.summary_variant import EffectDetail


# @pytest.mark.slow
# def test_annotate_variant_effects_ustudy(
#         ustudy, temp_filename, effect_annotator):
#
#     annotator = effect_annotator
#     vars_df = annotator.annotate(ustudy.annot_df, ustudy.vcf_vars)
#
#     stored_df = vars_df.copy()
#     RawVariantsLoader.save_annotation_file(
#         vars_df, temp_filename, storage='csv')
#     assert_annotation_equals(vars_df, stored_df)
#
#     vars1_df = RawVariantsLoader.load_annotation_file(
#         temp_filename, storage='csv')
#     assert_annotation_equals(vars_df, vars1_df)
#
#
# @pytest.mark.skip
# def test_annotate_variant_effects_nvcf(nvcf, effect_annotator):
#     annotator = effect_annotator
#     annotator.annotate(nvcf.annot_df, nvcf.vcf_vars)
#
#
# @pytest.mark.skip
# def test_annotate_variant_effects_uvcf(uvcf, effect_annotator):
#     annotator = effect_annotator
#     annotator.annotate(uvcf.annot_df, uvcf.vcf_vars)
#
#
# @pytest.mark.skip
# def test_annotate_variant_effects_fvcf(fvcf, effect_annotator):
#     annotator = effect_annotator
#     annotator.annotate(fvcf.annot_df, fvcf.vcf_vars)
#
#
# @pytest.mark.slow
# def test_annotator_variants_effects_csv_experiment(
#         nvcf19, temp_filename, effect_annotator):
#
#     annotator = effect_annotator
#     assert annotator is not None
#
#     annot_df = annotator.annotate(nvcf19.annot_df, nvcf19.vcf_vars)
#     assert annot_df is not None
#
#     stored_df = annot_df.copy()
#     RawVariantsLoader.save_annotation_file(
#         annot_df, temp_filename, storage='csv')
#     assert_annotation_equals(annot_df, stored_df)
#
#     vars1_df = RawVariantsLoader.load_annotation_file(
#         temp_filename, storage='csv')
#     assert_annotation_equals(annot_df, vars1_df)
#
#
# def test_effects_annotation(effect_annotator):
#     chrom, pos, ref, alts = (
#         "1",
#         874816,
#         'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT',
#         [
#             'C',
#             'CTCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT',
#             'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
#             'CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
#         ]
#     )
#
#     for alt in alts:
#         print("")
#         print("REF, ALT:>", ref, alt)
#         effects = effect_annotator.do_annotate_variant(chrom, pos, ref, alt)
#         for effect in effects:
#             print(
#                 ref, ",", alt, ":>",
#                 effect.gene,
#                 effect.transcript_id,
#                 effect.strand,
#                 effect.effect,
#                 effect.prot_pos,
#                 effect.prot_length,
#                 effect.aa_change
#             )
#
#
# @pytest.mark.parametrize("variant", [
#     "1:1558774:G:A",
#     "1:71418630:A:G",
#     "1:71439935:C:CG",
#     "1:186077583:T:G",
#     "1:186157005:C:T",
#     "1:186281435:A:G",
#     "2:234676519:C:T",
#     "13:111290774:C:T",
# ])
# def test_variant_effect_annotation(variant, effect_annotator):
#     [chrom, pos, ref, alts] = variant.split(":")
#     for alt in alts.split(','):
#         print("")
#         print("REF, ALT:>", ref, alt)
#         effects = effect_annotator.do_annotate_variant(
#             chrom, int(pos), ref, alt)
#         for effect in effects:
#             print(
#                 ref, ",", alt, ":>",
#                 effect.gene,
#                 effect.transcript_id,
#                 effect.strand,
#                 effect.effect,
#                 effect.prot_pos,
#                 effect.prot_length,
#                 effect.aa_change
#             )
#         print(effect_annotator.variant_annotator.effect_simplify(effects))


# @pytest.mark.parametrize("variant", [
#     "13:111290774:C:T",
# ])
# def test_variant_effect_annotation_test_transcript(
#         variant, effect_annotator_full):
#     effect_annotator = effect_annotator_full
#     [chrom, pos, ref, alts] = variant.split(":")
#     for alt in alts.split(','):
#         print("")
#         print("REF, ALT:>", ref, alt)
#         effects = effect_annotator.do_annotate_variant(
#             chrom, int(pos), ref, alt)
#         for effect in effects:
#             print(
#                 ref, ",", alt, ":>",
#                 effect.gene,
#                 effect.transcript_id,
#                 effect.strand,
#                 effect.effect,
#                 effect.prot_pos,
#                 effect.prot_length,
#                 effect.aa_change
#             )
#
#         res = effect_annotator_full.wrap_effects(effects)
#         print(res)
#
#         ed = EffectDetail.from_effects(*res)
#
#         print(ed.worst)
#         print(ed.gene)


def test_annotate_variant_effects_ustudy(
        nvcf19, temp_filename, effect_annotator_full):

    annotator = effect_annotator_full
    vars_df = annotator.annotate(nvcf19.annot_df, nvcf19.vcf_vars)

    print(vars_df.head())

    stored_df = vars_df.copy()
    RawVariantsLoader.save_annotation_file(
        vars_df, "annot.tmp", storage='csv')
    # assert_annotation_equals(vars_df, stored_df)

    vars1_df = RawVariantsLoader.load_annotation_file(
        "annot.tmp", storage='csv')
    # assert_annotation_equals(vars_df, vars1_df)
    print(vars1_df.head())

    # assert vars_df['effectType'].values == vars1_df["effectType"].values
