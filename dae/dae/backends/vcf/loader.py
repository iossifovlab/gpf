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
            params.get('vcf_include_reference_genotypes', False)
        self.include_unknown_family_genotypes = \
            params.get('vcf_include_unknown_family_genotypes', False)
        self.include_unknown_person_genotypes = \
            params.get('vcf_include_unknown_person_genotypes', False)
        self.multi_loader_fill_in_mode = \
            params.get('vcf_multi_loader_fill_in_mode', 'reference')

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

    def __init__(
            self, families, vcf_files,
            regions=None, fill_missing_ref=True, params={}):
        super(VcfLoader, self).__init__(
            families=families,
            filename=vcf_files[0],
            source_type='vcf',
            transmission_type=TransmissionType.transmitted,
            params=params)

        assert len(vcf_files)
        assert all([os.path.exists(fn) for fn in vcf_files])
        self.vcf_files = vcf_files

        if regions is None or isinstance(regions, str):
            self.regions = [regions]
        else:
            self.regions = regions

        self.fill_missing_value = 0 if fill_missing_ref else -1

        self._init_vcf_readers()

        samples = list()
        for vcf in self.vcfs:
            samples += vcf.samples
        samples = np.array(samples)

        self._match_pedigree_to_samples(families, samples)
        self._init_chromosome_order()

    def _init_vcf_readers(self):
        self.vcfs = list()
        for file in self.vcf_files:
            assert os.path.exists(file)
            self.vcfs.append(VCF(file, lazy=True))

    def _get_vcf_iterators(self, region):
        return [enumerate(vcf(region)) for vcf in self.vcfs]

    def _init_chromosome_order(self):
        seqnames = self.vcfs[0].seqnames
        assert all([vcf.seqnames == seqnames for vcf in self.vcfs])

        chrom_order = dict()
        for idx, seq in enumerate(seqnames):
            chrom_order[seq] = idx

        self.chrom_order = chrom_order

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

    def _build_summary_variant(self, summary_index, vcf_variant):
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

    def _compare_summaries_g(self, lhs, rhs):
        """
        Returns true if left summary variant position in file is
        larger than right summary variant position in file
        """
        # TODO: Change this to use a dict
        l_chrom_idx = self.chrom_order.get(lhs.ref_allele.chromosome)
        r_chrom_idx = self.chrom_order.get(rhs.ref_allele.chromosome)

        if l_chrom_idx > r_chrom_idx:
            return True
        elif lhs.ref_allele.position > rhs.ref_allele.position:
            return True
        else:
            return False

    def _find_min_summary_variant(self, summary_variants) -> int:
        assert len(summary_variants)
        min = 0
        for i in range(1, len(summary_variants)):
            if self._compare_summaries_g(
                    summary_variants[min],
                    summary_variants[i]):
                min = i
        return summary_variants[min]

    def _generate_missing_genotype(self, vcf):
        sample_count = len(vcf.samples)

        gt = np.array([[0] * 3] * sample_count, dtype=np.int8)

        gt[0:sample_count] = self.fill_missing_value

        return gt

    def _merge_genotypes(self, genotypes):
        """
        Merges a list of genotypes into one
        """
        out = None
        for gt in genotypes:
            if out is None:
                out = gt
            else:
                out = np.concatenate((out, gt))
        return out

    def _summary_genotypes_iterator_internal(self, vcf_iterators):
        vcf_variants = [next(it, None) for it in vcf_iterators]
        variant_count = 0

        while True:
            if all([vcf_variant is None for vcf_variant in vcf_variants]):
                break

            summary_variants = list(map(
                lambda x: self._build_summary_variant(variant_count, x[1]),
                vcf_variants
            ))

            current_summary_variant = \
                self._find_min_summary_variant(summary_variants)

            iterator_idxs_to_advance = list()
            genotypes = tuple()

            for idx, (sv, (_, vcf_variant)) in \
                    enumerate(zip(summary_variants, vcf_variants)):
                if sv == current_summary_variant:
                    genotypes += tuple(vcf_variant.genotypes)
                    iterator_idxs_to_advance.append(idx)
                else:
                    genotypes += tuple(
                        self._generate_missing_genotype(self.vcfs[idx])
                    )

            family_genotypes = VcfFamiliesGenotypes(
                self.families,
                np.array(genotypes, dtype=np.int8).T,
                params=self.params)

            yield current_summary_variant, family_genotypes

            for idx in iterator_idxs_to_advance:
                vcf_variants[idx] = next(vcf_iterators[idx], None)
            variant_count += 1

    def summary_genotypes_iterator(self):
        for region in self.regions:
            vcf_iterators = self._get_vcf_iterators(region)

            summary_genotypes = \
                self._summary_genotypes_iterator_internal(vcf_iterators)

            for summary_variant, family_genotypes in summary_genotypes:
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
        parser.add_argument(
            '--vcf-multi-loader-fill-in-mode', default='reference',
            dest='vcf_multi_loader_fill_in_mode',
            help='used for multi VCF files loader to fill missing genotypes; '
            'supported values are `reference` or `unknown`'
            '[default: %(default)s]',
        )

    @staticmethod
    def parse_cli_arguments(argv):
        multi_loader_fill_in_mode = argv.vcf_multi_loader_fill_in_mode
        assert multi_loader_fill_in_mode in set(['reference', 'unknown'])
        params = {
            'vcf_include_reference_genotypes': argv.vcf_include_reference,
            'vcf_include_unknown_family_genotypes': argv.vcf_include_unknown,
            'vcf_include_unknown_person_genotypes': argv.vcf_include_unknown,
            'vcf_multi_loader_fill_in_mode': multi_loader_fill_in_mode,
        }
        return params
