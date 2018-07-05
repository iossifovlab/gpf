'''
Created on Jul 5, 2018

@author: lubo
'''
from variants.annotate_composite import AnnotatorBase
from variants.vcf_utils import cshl_format
from variants.attributes import VariantType


class VcfVariantDetailsAnnotator(AnnotatorBase):
    COLUMNS = [
        'variant_type',
        'cshl_variant',
        'cshl_position',
        'cshl_length',
    ]

    def __init__(self):
        super(VcfVariantDetailsAnnotator, self).__init__()

    def annotate_variant(self, vcf_variant):
        variant_types = [0]
        cshl_variants = [None]
        cshl_positions = [-1]
        cshl_lengths = [-1]

        for alt in vcf_variant.ALT:

            cshl_pos, cshl_var, cshl_len = cshl_format(
                vcf_variant.start + 1,
                vcf_variant.REF, alt)
            variant_type = VariantType.from_cshl_variant(cshl_var)

            variant_types.append(variant_type.value)
            cshl_variants.append(cshl_var)
            cshl_positions.append(cshl_pos)
            cshl_lengths.append(cshl_len)

        return variant_types, cshl_variants, cshl_positions, cshl_lengths
