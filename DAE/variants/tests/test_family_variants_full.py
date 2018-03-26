'''
Created on Mar 26, 2018

@author: lubo
'''
from __future__ import print_function

from variants.vcf_utils import mat2str
from variants.attributes import Inheritance
from variants.variant_full import SummaryVariantFull, FamilyVariantFull


def test_family_variants_full(nvcf19f):
    for index, row in nvcf19f.annot_df.iterrows():
        sv = SummaryVariantFull.from_dict(row)
        assert sv is not None

    variants = nvcf19f.vcf_vars
    for index, row in enumerate(nvcf19f.annot_df.to_dict(orient='records')):
        vcf = variants[index]

        summary_variant = SummaryVariantFull.from_dict(row)

        if len(summary_variant.alt) <= 1:
            continue

        for fam in nvcf19f.families.values():
            vs = FamilyVariantFull.from_vcf(
                summary_variant, fam, vcf)
            for v in vs:
                if v.inheritance == Inheritance.reference:
                    continue
                print(v, v.family_id, mat2str(v.best_st))
