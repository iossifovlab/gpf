'''
Created on Jul 23, 2018

@author: lubo
'''
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariantFactory

from dae.backends.raw.raw_variants import RawFamilyVariants, TransmissionType


class BaseDAE(RawFamilyVariants):

    def __init__(self, families,
                 transmission_type,
                 source_filename=None):
        super(BaseDAE, self).__init__(
            families, transmission_type=transmission_type,
            source_filename=source_filename)


class RawDAE(BaseDAE):

    def __init__(
            self, families, annot_df, genotype_records,
            source_filename=None):

        super(RawDAE, self).__init__(
            families,
            transmission_type=TransmissionType.transmitted,
            source_filename=source_filename)

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
                v = FamilyVariant.from_summary_variant(
                    summary_variant, family, gt)
                family_variants.append(v)
            yield summary_variant, family_variants
