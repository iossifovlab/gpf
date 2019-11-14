'''
Created on Jul 23, 2018

@author: lubo
'''
import gzip
import os
import sys
import traceback
from contextlib import closing

import pysam

import numpy as np
import pandas as pd

from dae.utils.vcf_utils import best2gt, str2mat, reference_genotype
from dae.utils.dae_utils import dae2vcf_variant

from dae.variants.attributes import VariantType
from dae.pedigrees.family import FamiliesData, Family
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariantFactory, SummaryVariant

from dae.backends.raw.raw_variants import RawFamilyVariants, TransmissionType


class BaseDAE(RawFamilyVariants):

    def __init__(self, families,
                 transmission_type):
        super(BaseDAE, self).__init__(
            families, transmission_type=transmission_type)


class RawDenovo(BaseDAE):
    def __init__(self, families, denovo_df, annot_df):
        super(RawDenovo, self).__init__(
            families=families,
            transmission_type=TransmissionType.denovo)
        self.denovo_df = denovo_df
        self.annot_df = annot_df

        assert self.annot_df is not None
        assert len(self.denovo_df) == len(self.annot_df)

    def full_variants_iterator(self, return_reference=False):
        denovo = self.denovo_df.to_dict(orient='records')
        annot = self.annot_df.to_dict(orient='records')

        for index, (arow, drow) in enumerate(zip(annot, denovo)):
            try:
                summary_variant = SummaryVariantFactory \
                    .summary_variant_from_records(
                        [arow], transmission_type=self.transmission_type)

                gt = drow['genotype']
                family_id = drow['family_id']
                family = self.families.get_family(family_id)
                assert family is not None

                assert len(family) == gt.shape[1], \
                    (family.family_id, len(family), gt.shape)

                family_variant = FamilyVariant.from_sumary_variant(
                    summary_variant, family, gt)

                yield summary_variant, [family_variant]
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", arow, drow, index)
                traceback.print_exc(file=sys.stdout)


class RawDAE(BaseDAE):

    def __init__(self, families, annot_df, genotype_records):

        super(RawDAE, self).__init__(
            families,
            transmission_type=TransmissionType.transmitted)

        assert len(annot_df) == 2 * len(genotype_records), \
            "{} == 2 * {}".format(len(annot_df), len(genotype_records))

        self.annot_df = annot_df
        self.genotype_records = genotype_records

    def wrap_summary_variant(self, records):
        return SummaryVariantFactory.summary_variant_from_records(
            records,
            transmission_type=self.transmission_type)

    def full_variants_iterator(self, return_reference=False):
        sum_df = self.annot_df
        for summary_index, group_df in \
                sum_df.groupby("summary_variant_index"):
            genotype_record = self.genotype_records[summary_index]
            summary_variant = self.wrap_summary_variant(
                group_df.to_dict(orient='records'))

            family_variants = []
            assert len(genotype_record) == len(self.families.families_list())
            for family, gt in zip(
                    self.families.families_list(), genotype_record):
                v = FamilyVariant.from_sumary_variant(
                    summary_variant, family, gt)
                family_variants.append(v)
            yield summary_variant, family_variants
