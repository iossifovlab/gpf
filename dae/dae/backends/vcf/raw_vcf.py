from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

from dae.backends.raw.raw_variants import RawFamilyVariants, TransmissionType


class VariantFactory(SummaryVariantFactory):

    @staticmethod
    def from_summary_variant(sv, family, gt):
        return FamilyVariant.from_sumary_variant(sv, family, gt)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        assert vcf is not None
        # assert isinstance(family, VcfFamily)

        # gt = vcf.gt_idxs[family.alleles].\
        #     astype(GENOTYPE_TYPE, casting='same_kind')
        # gt = gt.reshape([2, len(family)], order='F')

        gt = vcf.gt[:, family.samples]
        assert gt.shape == (2, len(family))

        return VariantFactory.from_summary_variant(
            summary_variant, family, gt)


class RawVcfVariants(RawFamilyVariants):

    def __init__(self, families, vcf, annot_df,
                 transmission_type=TransmissionType.transmitted,
                 variant_factory=VariantFactory,
                 source_filename=None):

        super(RawVcfVariants, self).__init__(
            families,
            transmission_type=transmission_type,
            source_filename=source_filename)

        assert annot_df is not None

        self.VF = variant_factory
        self.vcf = vcf
        self.annot_df = annot_df

    def is_empty(self):
        return len(self.annot_df) == 0

    def wrap_summary_variant(self, records):
        return self.VF.summary_variant_from_records(
            records,
            transmission_type=self.transmission_type)

    def full_variants_iterator(self):
        sum_df = self.annot_df
        variants = self.vcf.vars
        for summary_index, group_df in \
                sum_df.groupby("summary_variant_index"):
            vcf = variants[summary_index]
            summary_variant = self.wrap_summary_variant(
                group_df.to_dict(orient='records'))

            family_variants = []
            for fam in self.families.families_list():
                v = self.VF.family_variant_from_vcf(
                    summary_variant, fam, vcf=vcf)
                family_variants.append(v)
            yield summary_variant, family_variants
