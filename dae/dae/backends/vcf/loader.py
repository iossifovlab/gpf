import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

from dae.pedigrees.family import FamiliesData
from dae.variants.variant import SummaryVariantFactory
from dae.backends.raw.loader import VariantsLoader


class VcfLoader(VariantsLoader):

    def __init__(self, families, vcf_filename, region=None):
        assert os.path.exists(vcf_filename)
        self.vcf_filename = vcf_filename

        self.vcf = VCF(vcf_filename, lazy=True)
        samples = np.array(self.vcf.samples)

        ped_df, samples = self._match_pedigree_to_samples(
            families.ped_df, samples)
        self.families = FamiliesData.from_pedigree_df(ped_df)
        self.samples = samples

    @staticmethod
    def _match_pedigree_to_samples(ped_df, samples):
        vcf_samples = list(samples)
        samples_needed = set(samples)
        pedigree_samples = set(ped_df['sample_id'].values)
        missing_samples = samples_needed.difference(pedigree_samples)

        samples_needed = samples_needed.difference(missing_samples)
        assert samples_needed.issubset(pedigree_samples)

        pedigree = []
        seen = set()
        for record in ped_df.to_dict(orient='record'):
            if record['sample_id'] in samples_needed:
                if record['sample_id'] in seen:
                    continue
                record['samples_index'] = \
                    vcf_samples.index(record['sample_id'])
                pedigree.append(record)
                seen.add(record['sample_id'])

        assert len(pedigree) == len(samples_needed)

        pedigree_order = list(ped_df['sample_id'].values)
        pedigree = sorted(
            pedigree, key=lambda p: pedigree_order.index(p['sample_id']))

        ped_df = pd.DataFrame(pedigree)
        return ped_df, ped_df['sample_id'].values

    def _warp_summary_variant(self, summary_index, vcf_variant):
        records = []
        allele_count = len(vcf_variant.ALT) + 1
        records.append(
            {
                'chrom': vcf_variant.CHROM,
                'position': vcf_variant.start + 1,
                'reference': vcf_variant.REF,
                'alternative': None,
                'summary_variant_index': summary_index,
                'allele_index': 0,
                'allele_count': allele_count
            }
        )
        for allele_index, alt in enumerate(vcf_variant.ALT):
            records.append(
                {
                    'chrom': vcf_variant.CHROM,
                    'position': vcf_variant.start + 1,
                    'reference': vcf_variant.REF,
                    'alternative': alt,
                    'summary_variant_index': summary_index,
                    'allele_index': allele_index + 1,
                    'allele_count': allele_count
                }
            )
        return SummaryVariantFactory.summary_variant_from_records(records)

    def summary_genotypes_iterator(self):
        for summary_index, vcf_variant in enumerate(self.vcf):
            family_genotypes = np.array(vcf_variant.genotypes, dtype=np.int8).T

            summary_variant = self._warp_summary_variant(
                summary_index, vcf_variant)

            yield summary_variant, family_genotypes
