'''
Created on Jul 5, 2018

@author: lubo
'''
from __future__ import unicode_literals, absolute_import

from utils.vcf_utils import cshl_format
from variants.attributes import VariantType

from .annotate_composite import AnnotatorBase


class VcfVariantDetailsAnnotator(AnnotatorBase):
    COLUMNS = [
        'variant_type',
        'cshl_variant',
        'cshl_position',
        'cshl_length',
    ]

    def __init__(self):
        super(VcfVariantDetailsAnnotator, self).__init__()

    def annotate_variant_allele(self, allele):
        if allele['alternative'] is None:

            variant_types = 0
            cshl_variants = None
            cshl_positions = -1
            cshl_lengths = -1
        else:
            cshl_pos, cshl_var, cshl_len = cshl_format(
                allele['position'],
                allele['reference'],
                allele['alternative'])
            variant_type = VariantType.from_cshl_variant(cshl_var)

            variant_types = variant_type.value
            cshl_variants = cshl_var
            cshl_positions = cshl_pos
            cshl_lengths = cshl_len

        return variant_types, cshl_variants, cshl_positions, cshl_lengths
