import os

from cyvcf2 import VCF

import numpy as np

from dae.utils.variant_utils import is_all_reference_genotype, \
    is_all_unknown_genotype, is_unknown_genotype
from dae.variants.variant import SummaryVariantFactory
from dae.backends.raw.loader import VariantsLoader, TransmissionType, \
    FamiliesGenotypes


class VcfFamiliesGenotypes(FamiliesGenotypes):

    def __init__(self, families, families_genotypes, params={}):
        super(VcfFamiliesGenotypes, self).__init__()
        self.families = families
        self.families_genotypes = families_genotypes
        self.include_reference_genotypes = \
            params.get('include_reference_genotypes', False)
        self.include_unknown_family_genotypes = \
            params.get('include_unknown_family_genotypes', False)
        self.include_unknown_person_genotypes = \
            params.get('include_unknown_person_genotypes', False)

    def get_family_genotype(self, family):
        gt = self.families_genotypes[0:2, family.samples_index]
        assert gt.shape == (2, len(family)), \
            f"{gt.shape} == (2, {len(family)})"
        return gt

    def family_genotype_iterator(self):
        for fam in self.families.values():
            if len(fam) == 0:
                continue
            gt = self.get_family_genotype(fam)
            if is_all_reference_genotype(gt) \
                    and not self.include_reference_genotypes:
                continue
            if is_unknown_genotype(gt) \
                    and not self.include_unknown_person_genotypes:
                continue
            if is_all_unknown_genotype(gt) \
                    and not self.include_unknown_family_genotypes:
                continue

            yield fam, gt

    def full_families_genotypes(self):
        return self.families_genotypes


class VcfLoader(VariantsLoader):

    def __init__(self, families, vcf_filename, regions=None, params={}):
        super(VcfLoader, self).__init__(
            families=families,
            filename=vcf_filename,
            source_type='vcf',
            transmission_type=TransmissionType.transmitted,
            params=params)

        assert os.path.exists(vcf_filename)
        self.vcf_filename = vcf_filename
        if regions is None or isinstance(regions, str):
            self.regions = [regions]
        else:
            self.regions = regions

        self.vcf = VCF(self.filename, lazy=True)
        samples = np.array(self.vcf.samples)

        self._match_pedigree_to_samples(families, samples)

    @staticmethod
    def _match_pedigree_to_samples(families, vcf_samples):
        vcf_samples_index = list(vcf_samples)
        vcf_samples = set(vcf_samples)
        pedigree_samples = set(families.ped_df['sample_id'].values)
        missing_samples = vcf_samples.difference(pedigree_samples)

        vcf_samples = vcf_samples.difference(missing_samples)
        assert vcf_samples.issubset(pedigree_samples)

        seen = set()
        for person_id, person in families.persons.items():
            if person.sample_id in vcf_samples:
                if person.sample_id in seen:
                    continue
                person.sample_index = \
                    vcf_samples_index.index(person.sample_id)
                seen.add(person.sample_id)
            else:
                person._generated = True
                families[person.family_id].redefine()

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
        for region in self.regions:
            for summary_index, vcf_variant in enumerate(self.vcf(region)):
                family_genotypes = VcfFamiliesGenotypes(
                    self.families,
                    np.array(vcf_variant.genotypes, dtype=np.int8).T,
                    params=self.params)

                summary_variant = self._warp_summary_variant(
                    summary_index, vcf_variant)

                yield summary_variant, family_genotypes

    @staticmethod
    def cli_arguments(parser):
        parser.add_argument(
            '--vcf-include-reference', default=False,
            dest='vcf_include_reference',
            help='include reference only variants [default: %(default)s]',
            action='store_true'
        )
        parser.add_argument(
            '--vcf-include-unknown', default=False,
            dest='vcf_include_unknown',
            help='include variants with unknown genotype '
            '[default: %(default)s]',
            action='store_true'
        )

    @staticmethod
    def parse_cli_arguments(argv):
        params = {
            'include_reference_genotypes': argv.vcf_include_reference,
            'include_unknown_family_genotypes': argv.vcf_include_unknown,
            'include_unknown_person_genotypes': argv.vcf_include_unknown
        }
        return params
