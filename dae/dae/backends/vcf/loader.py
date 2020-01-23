import sys
from cyvcf2 import VCF

import numpy as np

from dae.GenomeAccess import GenomicSequence

from dae.utils.helpers import str2bool

from dae.utils.variant_utils import is_all_reference_genotype, \
    is_all_unknown_genotype, is_unknown_genotype, GENOTYPE_TYPE
from dae.variants.attributes import Inheritance
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.backends.raw.loader import VariantsGenotypesLoader, \
    TransmissionType, \
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

    def get_family_best_state(self, family):
        return None

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
            bs = self.get_family_best_state(fam)

            yield fam, gt, bs

    def full_families_genotypes(self):
        return self.families_genotypes


class VcfLoader(VariantsGenotypesLoader):

    def __init__(
            self,
            families,
            vcf_files,
            genome: GenomicSequence,
            regions=None,
            params={},
            **kwargs):
        super(VcfLoader, self).__init__(
            families=families,
            filenames=vcf_files,
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            overwrite=False,
            expect_genotype=True,
            expect_best_state=False,
            params=params)

        assert len(vcf_files)
        self.reset_regions(regions)
        fill_in_mode = params.get(
            "vcf_multi_loader_fill_in_mode", "reference")
        if fill_in_mode == 'reference':
            self._fill_missing_value = 0
        elif fill_in_mode == 'unknown':
            self._fill_missing_value = -1
        else:
            print(
                f"unexpected `vcf_multi_loader_fill_in_mode` value",
                f"{fill_in_mode}; "
                f"expected values are `reference` or `unknown`",
                file=sys.stderr)
            self._fill_missing_value = 0
        self._init_vcf_readers()

        samples = list()
        for vcf in self.vcfs:
            samples += vcf.samples
        samples = np.array(samples)

        self._match_pedigree_to_samples(families, samples)

        self._init_chromosome_order()
        self.set_attribute('source_type', 'vcf')
        self._init_denovo_mode()
        self._init_omission_mode()

    def _init_denovo_mode(self):
        denovo_mode = self.params.get('vcf_denovo_mode', 'possible_denovo')
        if denovo_mode == 'possible_denovo':
            self._denovo_handler = self._possible_denovo_mode_handler
        elif denovo_mode == 'denovo':
            self._denovo_handler = self._denovo_mode_handler
        elif denovo_mode == 'ignore':
            self._denovo_handler = self._ignore_denovo_mode_handler
        else:
            print(
                f"unexpected denovo mode: {denovo_mode}; "
                f"using possible_denovo")
            self._denovo_handler = self._possible_denovo_mode_handler

    @staticmethod
    def _possible_denovo_mode_handler(
            family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            inheritance_in_members = fa.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.denovo else Inheritance.possible_denovo
                for inh in inheritance_in_members
            ]
            fa._inheritance_in_members = inheritance_in_members
        return False

    @staticmethod
    def _ignore_denovo_mode_handler(
            family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            if Inheritance.denovo in fa.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _denovo_mode_handler(
            family_vairant: FamilyVariant) -> bool:
        return False

    def _init_omission_mode(self):
        omission_mode = self.params.get(
            'vcf_omission_mode', 'possible_omission')
        if omission_mode == 'possible_omission':
            self._omission_handler = self._possible_omission_mode_handler
        elif omission_mode == 'omission':
            self._omission_handler = self._omission_mode_handler
        elif omission_mode == 'ignore':
            self._omission_handler = self._ignore_omission_mode_handler
        else:
            print(
                f"unexpected omission mode: {omission_mode}; "
                f"using possible_omission")
            self._omission_handler = self._possible_omission_mode_handler

    @staticmethod
    def _possible_omission_mode_handler(
            family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            inheritance_in_members = fa.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.omission
                else Inheritance.possible_omission
                for inh in inheritance_in_members
            ]
            fa._inheritance_in_members = inheritance_in_members
        return False

    @staticmethod
    def _ignore_omission_mode_handler(
            family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            print(
                "ignore_omission:",
                Inheritance.omission, fa.inheritance_in_members)
            if Inheritance.omission in fa.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _omission_mode_handler(
            family_vairant: FamilyVariant) -> bool:
        return False

    def reset_regions(self, regions):
        if regions is None or isinstance(regions, str):
            self.regions = [regions]
        else:
            self.regions = regions

    def _init_vcf_readers(self):
        self.vcfs = list()
        for file in self.filenames:
            self.vcfs.append(VCF(file, lazy=True))

    def _build_vcf_iterators(self, region):
        return [vcf(region) for vcf in self.vcfs]

    def _init_chromosome_order(self):
        seqnames = self.vcfs[0].seqnames
        assert all([vcf.seqnames == seqnames for vcf in self.vcfs])

        chrom_order = dict()
        for idx, seq in enumerate(seqnames):
            chrom_order[seq] = idx

        self.chrom_order = chrom_order
        self.chromosomes = seqnames

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
        families.redefine()

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

    def _compare_vcf_variants_gt(self, lhs, rhs):
        """
        Returns true if left vcf variant position in file is
        larger than right vcf variant position in file
        """
        # TODO: Change this to use a dict
        l_chrom_idx = self.chrom_order.get(lhs.CHROM)
        r_chrom_idx = self.chrom_order.get(rhs.CHROM)

        if l_chrom_idx > r_chrom_idx:
            return True
        elif lhs.POS > rhs.POS:
            return True
        else:
            return False

    def _compare_vcf_variants_eq(self, lhs, rhs):
        """
        Returns true if left vcf variant position in file is
        equal to right vcf variant position in file
        """
        return lhs.CHROM == rhs.CHROM and lhs.POS == rhs.POS

    def _find_current_vcf_variant(self, vcf_variants):
        assert len(vcf_variants)
        min_index = 0
        for index in range(1, len(vcf_variants)):
            if vcf_variants[index] is None:
                continue
            if self._compare_vcf_variants_gt(
                    vcf_variants[min_index],
                    vcf_variants[index]):
                min_index = index
        return vcf_variants[min_index]

    def _generate_missing_genotype(self, vcf):
        sample_count = len(vcf.samples)

        gt = np.array([[0] * 3] * sample_count, dtype=np.int8)

        gt[0:sample_count] = self._fill_missing_value

        return gt

    def _full_variants_iterator_impl(self):
        summary_variant_index = 0
        for region in self.regions:
            vcf_iterators = self._build_vcf_iterators(region)
            vcf_variants = [next(it, None) for it in vcf_iterators]

            while True:
                if all([vcf_variant is None for vcf_variant in vcf_variants]):
                    break

                current_vcf_variant = \
                    self._find_current_vcf_variant(vcf_variants)
                current_summary_variant = self._build_summary_variant(
                    summary_variant_index, current_vcf_variant)

                vcf_iterator_idexes_to_advance = list()
                genotypes = tuple()
                for idx, vcf_variant in enumerate(vcf_variants):
                    if self._compare_vcf_variants_eq(
                            current_vcf_variant, vcf_variant):
                        genotypes += tuple(vcf_variant.genotypes)
                        vcf_iterator_idexes_to_advance.append(idx)
                    else:
                        genotypes += tuple(
                            self._generate_missing_genotype(self.vcfs[idx])
                        )

                family_genotypes = VcfFamiliesGenotypes(
                    self.families,
                    VcfLoader.transform_vcf_genotypes(genotypes),
                    params=self.params)

                family_variants = []
                for fam, gt, bs in family_genotypes.family_genotype_iterator():
                    fv = FamilyVariant(current_summary_variant, fam, gt, bs)
                    if self._denovo_handler(fv):
                        continue
                    if self._omission_handler(fv):
                        continue
                    family_variants.append(fv)

                yield current_summary_variant, family_variants

                for idx in vcf_iterator_idexes_to_advance:
                    vcf_variants[idx] = next(vcf_iterators[idx], None)
                summary_variant_index += 1

    @staticmethod
    def transform_vcf_genotypes(genotypes):
        new_genotypes = []
        for genotype in genotypes:
            if len(genotype) == 2:  # Handle haploid genotypes
                genotype.insert(1, -2)
            new_genotypes.append(genotype)
        return np.array(new_genotypes, dtype=GENOTYPE_TYPE).T

    @staticmethod
    def cli_defaults():
        return {
            'vcf_include_reference_genotypes': False,
            'vcf_include_unknown_family_genotypes': False,
            'vcf_include_unknown_person_genotypes': False,
            'vcf_multi_loader_fill_in_mode': 'reference',
            'vcf_denovo_mode': 'possible_denovo',
            'vcf_omission_mode': 'possible_omission',
        }

    @staticmethod
    def build_cli_arguments(params):
        param_defaults = VcfLoader.cli_defaults()
        result = []
        for key, value in params.items():
            assert key in param_defaults, (key, list(param_defaults.keys()))
            if value != param_defaults[key]:
                param = key.replace('_', '-')
                if key in {'vcf_multi_loader_fill_in_mode',
                           'vcf_denovo_mode',
                           'vcf_omission_mode'}:
                    result.append(f'--{param}')
                    result.append(f'{value}')
                else:
                    if value:
                        result.append(f'--{param}')
        return ' '.join(result)

    @staticmethod
    def cli_arguments(parser):
        parser.add_argument(
            'vcf_files', type=str, nargs='+',
            metavar='<VCF filenames>',
            help='VCF files to import'
        )
        VcfLoader.cli_options(parser)

    @staticmethod
    def cli_options(parser):
        parser.add_argument(
            '--vcf-include-reference-genotypes', default=False,
            dest='vcf_include_reference_genotypes',
            help='include reference only variants [default: %(default)s]',
            action='store_true'
        )
        parser.add_argument(
            '--vcf-include-unknown-family-genotypes', default=False,
            dest='vcf_include_unknown_family_genotypes',
            help='include family variants with fully unknown genotype '
            '[default: %(default)s]',
            action='store_true'
        )
        parser.add_argument(
            '--vcf-include-unknown-person-genotypes', default=False,
            dest='vcf_include_unknown_person_genotypes',
            help='include family variants with partially unknown genotype '
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
        parser.add_argument(
            '--vcf-denovo-mode', default='possible_denovo',
            dest='vcf_denovo_mode',
            help='used for handling family variants with denovo inheritance; '
            'supported values are: `denovo`, `possible_denovo`, `ignore`; '
            '[default: %(default)s]',
        )
        parser.add_argument(
            '--vcf-omission-mode', default='possible_omission',
            dest='vcf_omission_mode',
            help='used for handling family variants with omission '
            'inheritance; '
            'supported values are: `omission`, `possible_omission`, `ignore`; '
            '[default: %(default)s]',
        )

    @staticmethod
    def parse_cli_arguments(argv):
        filenames = argv.vcf_files

        assert argv.vcf_multi_loader_fill_in_mode \
            in set(['reference', 'unknown'])
        assert argv.vcf_denovo_mode \
            in set(['denovo', 'possible_denovo', 'ignore']), \
            argv.vcf_denovo_mode
        assert argv.vcf_omission_mode \
            in set(['omission', 'possible_omission', 'ignore']), \
            argv.vcf_omission_mode
        params = {
            'vcf_include_reference_genotypes':
            str2bool(argv.vcf_include_reference_genotypes),
            'vcf_include_unknown_family_genotypes':
            str2bool(argv.vcf_include_unknown_family_genotypes),
            'vcf_include_unknown_person_genotypes':
            str2bool(argv.vcf_include_unknown_person_genotypes),
            'vcf_multi_loader_fill_in_mode':
            argv.vcf_multi_loader_fill_in_mode,
            'vcf_denovo_mode':
            argv.vcf_denovo_mode,
            'vcf_omission_mode':
            argv.vcf_omission_mode,
        }
        return filenames, params
