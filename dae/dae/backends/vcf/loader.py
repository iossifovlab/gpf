import os
from copy import deepcopy

from cyvcf2 import VCF

import numpy as np

from typing import List, Dict
from dae.pedigrees.family import FamiliesData

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


class MultiVcfLoader(VariantsLoader):

    def __init__(
            self,
            families: FamiliesData,
            vcf_files: List[str],
            reference_on_missing: bool = True,
            regions=None,
            params: Dict[str, bool] = {}):

        super(MultiVcfLoader, self).__init__(
            families=families,
            filename=vcf_files[0],
            source_type='vcf',
            transmission_type=TransmissionType.transmitted,
            params=params
        )

        self.families = families
        self.vcf_files = vcf_files
        self.reference_on_missing = reference_on_missing
        self.fill_missing_value = 0 if reference_on_missing else -1
        self.regions = regions
        self.vcf_loaders = list()
        self._init_loaders()
        self.seqnames = self._init_chromosome_order()

        # TODO: Find a better place for VcfLoader's _match_pedigree_to_samples
        # method
        VcfLoader._match_pedigree_to_samples(
                self.families,
                self._get_all_samples())

    def _init_loaders(self):
        for vcf_file in self.vcf_files:
            loader_families = deepcopy(self.families)

            loader = VcfLoader(
                loader_families,
                vcf_file,
                regions=self.regions,
                params=self.params)

            self.vcf_loaders.append(loader)

    def _init_chromosome_order(self) -> List[str]:
        seqnames = list()

        seqnames = self.vcf_loaders[0].vcf.seqnames
        assert \
            all([l.vcf.seqnames == seqnames for l in self.vcf_loaders])

        return seqnames

    def _get_all_samples(self):
        samples = list()
        for loader in self.vcf_loaders:
            samples += loader.vcf.samples
        return samples

    def _generate_missing_vcf_families_genotype(
            self, loader: VcfLoader):
        sample_count = len(loader.vcf.samples)
        gt = np.array(
            [[0] * 3] * sample_count, dtype=np.int8).T
        gt[0:2] = self.fill_missing_value
        return VcfFamiliesGenotypes(
            loader.families,
            gt,
            params=loader.params
        )

    def _merge_summary_genotypes(self, summary_variant, genotypes):
        sv = summary_variant
        gt_values = tuple()
        for gt in genotypes:
            gt_values += tuple(gt.T)
        gt = np.stack(gt_values).T
        gt = VcfFamiliesGenotypes(self.families, gt, self.params)
        return sv, gt

    def _fill_missing_family_genotypes(
            self, missing_variant_indexes, summary_genotypes, iterators):
        genotypes = list()
        for idx, summary_gt in enumerate(summary_genotypes):
            if idx not in missing_variant_indexes:
                genotypes.append(
                    summary_gt[1].full_families_genotypes()
                )
                summary_genotypes[idx] = \
                    next(iterators[idx], None)
            else:
                missing_raw_gt = \
                    self._generate_missing_vcf_families_genotype(
                        self.vcf_loaders[idx])

                missing_gt = \
                    missing_raw_gt.full_families_genotypes()

                genotypes.append(missing_gt)

        return genotypes

    def _compare_summaries_g(self, lhs, rhs):
        """
        Returns true if left summary variant position in file is
        larger than right summary variant position in file
        """
        l_chrom_idx = self.seqnames.index(lhs.ref_allele.chromosome)
        r_chrom_idx = self.seqnames.index(rhs.ref_allele.chromosome)

        if l_chrom_idx > r_chrom_idx:
            return True
        elif lhs.ref_allele.position > rhs.ref_allele.position:
            return True
        else:
            return False

    def _find_min_summary_index(self, summary_genotypes) -> int:
        assert len(summary_genotypes)
        min = 0
        for i in range(1, len(summary_genotypes)):
            if self._compare_summaries_g(
                    summary_genotypes[min][0],
                    summary_genotypes[i][0]):
                min = i
        return min

    def summary_genotypes_iterator(self):
        sum_gt_iterators = \
            [l.summary_genotypes_iterator() for l in self.vcf_loaders]

        current_summary_genotypes = [next(it, None) for it in sum_gt_iterators]
        while True:
            if all(sum_gt is None for sum_gt in current_summary_genotypes):
                break

            sum_gt_missing_stack = list()

            min_summary_variant_idx = \
                self._find_min_summary_index(current_summary_genotypes)
            min_summary_variant = \
                current_summary_genotypes[min_summary_variant_idx][0]

            for idx, sum_gt in enumerate(current_summary_genotypes):
                if(sum_gt[0] != min_summary_variant):
                    sum_gt_missing_stack.append(idx)

            if len(sum_gt_missing_stack):

                genotypes = self._fill_missing_family_genotypes(
                    sum_gt_missing_stack,
                    current_summary_genotypes,
                    sum_gt_iterators)

                yield self._merge_summary_genotypes(
                    min_summary_variant, genotypes)

                continue

            summaries, genotypes = zip(*current_summary_genotypes)

            genotypes = \
                list(map(
                    lambda x: x.full_families_genotypes(), genotypes))

            yield self._merge_summary_genotypes(summaries[0], genotypes)

            current_summary_genotypes = \
                [next(it, None) for it in sum_gt_iterators]
