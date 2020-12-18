import os
import sys
import itertools
import glob
import logging

import numpy as np

from cyvcf2 import VCF
import pysam

from dae.utils.helpers import str2bool
from dae.genome.genomes_db import Genome

from dae.utils.variant_utils import (
    is_all_reference_genotype,
    is_all_unknown_genotype,
    is_unknown_genotype,
)
from dae.variants.attributes import Inheritance
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.backends.raw.loader import VariantsGenotypesLoader, \
    TransmissionType, \
    FamiliesGenotypes, \
    CLIArgument


logger = logging.getLogger(__name__)


class VcfFamiliesGenotypes(FamiliesGenotypes):
    def __init__(self, loader, vcf_variants):
        super(VcfFamiliesGenotypes, self).__init__()

        self.loader = loader
        self.vcf_variants = vcf_variants

    def _build_genotypes(self):
        genotypes = []
        for vcf_index, vcf_variant in enumerate(self.vcf_variants):
            if vcf_variant is not None:
                # genotypes.append(vcf_variant.genotypes)
                current_vcf = self.loader.vcfs[vcf_index]
                samples_count = len(current_vcf.samples)
                logger.debug(
                    f"samples len: {samples_count}; "
                    f"gt_idxs: {len(vcf_variant.gt_idxs)}; "
                    f"{set(vcf_variant.gt_idxs)}")

                if len(vcf_variant.gt_idxs) == samples_count and \
                        set(vcf_variant.gt_idxs) == set([-1]):
                    gt_idxs = -1 * np.ones(2 * samples_count, dtype=np.int)
                else:
                    gt_idxs = vcf_variant.gt_idxs

                gt = gt_idxs
                gt[gt < -1] = -2
                genotypes.append(gt_idxs)
            else:
                fill_value = self.loader._fill_missing_value
                samples_count = len(self.loader.vcfs[vcf_index].samples)
                genotypes.append(
                    fill_value * np.ones(2 * samples_count, dtype=np.int16)
                )
        genotypes = np.hstack(genotypes)
        return genotypes.astype(np.int8)

    def family_genotype_iterator(self):
        genotypes = self._build_genotypes()

        # fmt: off
        for family, allele_indexes in \
                self.loader.families_allele_indexes:
            # fmt: on

            gt = genotypes[allele_indexes]
            gt = gt.reshape([2, len(allele_indexes)//2], order="F")

            if (
                is_all_reference_genotype(gt)
                and not self.loader.include_reference_genotypes
            ):
                continue
            if (
                is_unknown_genotype(gt)
                and not self.loader.include_unknown_person_genotypes
            ):
                continue
            if (
                is_all_unknown_genotype(gt)
                and not self.loader.include_unknown_family_genotypes
            ):
                continue

            yield family, gt, None


class SingleVcfLoader(VariantsGenotypesLoader):
    def __init__(
            self,
            families,
            vcf_files,
            genome: Genome,
            regions=None,
            params={},
            **kwargs):

        super(SingleVcfLoader, self).__init__(
            families=families,
            filenames=vcf_files,
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            regions=regions,
            expect_genotype=True,
            expect_best_state=False,
            params=params)

        assert len(vcf_files)
        self.set_attribute("source_type", "vcf")

        fill_in_mode = params.get("vcf_multi_loader_fill_in_mode", "reference")
        if fill_in_mode == "reference":
            self._fill_missing_value = 0
        elif fill_in_mode == "unknown":
            self._fill_missing_value = -1
        else:
            print(
                "unexpected `vcf_multi_loader_fill_in_mode` value",
                f"{fill_in_mode}; "
                f"expected values are `reference` or `unknown`",
                file=sys.stderr,
            )
            self._fill_missing_value = 0

        self._init_vcf_readers()
        self._match_pedigree_to_samples()
        self._build_family_alleles_indexes()
        self._build_independent_persons_indexes()
        self._init_chromosome_order()
        self._init_denovo_mode()
        self._init_omission_mode()

        self.include_reference_genotypes = str2bool(
            params.get("vcf_include_reference_genotypes", False)
        )
        self.include_unknown_family_genotypes = str2bool(
            params.get("vcf_include_unknown_family_genotypes", False)
        )
        self.include_unknown_person_genotypes = str2bool(
            params.get("vcf_include_unknown_person_genotypes", False)
        )
        self.multi_loader_fill_in_mode = params.get(
            "vcf_multi_loader_fill_in_mode", "reference"
        )

    def _init_denovo_mode(self):
        denovo_mode = self.params.get("vcf_denovo_mode", "possible_denovo")
        if denovo_mode == "possible_denovo":
            self._denovo_handler = self._possible_denovo_mode_handler
        elif denovo_mode == "denovo":
            self._denovo_handler = self._denovo_mode_handler
        elif denovo_mode == "ignore":
            self._denovo_handler = self._ignore_denovo_mode_handler
        else:
            print(
                f"unexpected denovo mode: {denovo_mode}; "
                f"using possible_denovo"
            )
            self._denovo_handler = self._possible_denovo_mode_handler

    @staticmethod
    def _possible_denovo_mode_handler(family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            inheritance_in_members = fa.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.denovo
                else Inheritance.possible_denovo
                for inh in inheritance_in_members
            ]
            fa._inheritance_in_members = inheritance_in_members
        return False

    @staticmethod
    def _ignore_denovo_mode_handler(family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            if Inheritance.denovo in fa.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _denovo_mode_handler(family_vairant: FamilyVariant) -> bool:
        return False

    def _init_omission_mode(self):
        omission_mode = self.params.get(
            "vcf_omission_mode", "possible_omission"
        )
        if omission_mode == "possible_omission":
            self._omission_handler = self._possible_omission_mode_handler
        elif omission_mode == "omission":
            self._omission_handler = self._omission_mode_handler
        elif omission_mode == "ignore":
            self._omission_handler = self._ignore_omission_mode_handler
        else:
            print(
                f"unexpected omission mode: {omission_mode}; "
                f"using possible_omission"
            )
            self._omission_handler = self._possible_omission_mode_handler

    @staticmethod
    def _possible_omission_mode_handler(family_variant: FamilyVariant) -> bool:
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
    def _ignore_omission_mode_handler(family_variant: FamilyVariant) -> bool:
        for fa in family_variant.alleles:
            if Inheritance.omission in fa.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _omission_mode_handler(family_vairant: FamilyVariant) -> bool:
        return False

    def _init_vcf_readers(self):
        self.vcfs = list()
        for file in self.filenames:
            self.vcfs.append(VCF(file, gts012=True, strict_gt=True, lazy=True))

    def _build_vcf_iterators(self, region):
        # print(f"build vcf iterator for {self.filenames} for region:", region)
        return [vcf(region) for vcf in self.vcfs]

    def _init_chromosome_order(self):
        seqnames = self.vcfs[0].seqnames
        if not all([vcf.seqnames == seqnames for vcf in self.vcfs]):
            logger.warning(
                f"VCF files {self.filenames} do not have the same list "
                f"of contigs")
            # assert all([vcf.seqnames == seqnames for vcf in self.vcfs]), \
            #     (self.filenames, seqnames)

        chrom_order = dict()
        for idx, seq in enumerate(seqnames):
            chrom_order[seq] = idx

        self.chrom_order = chrom_order

    @property
    def chromosomes(self):
        assert len(self.vcfs) > 0

        seqnames = self.vcfs[0].seqnames
        filename = self.filenames[0]
        tabix_index_filename = f"{filename}.tbi"
        if not os.path.exists(tabix_index_filename):
            return seqnames

        try:
            with pysam.Tabixfile(filename) as tbx:
                return list(tbx.contigs)
        except Exception:
            return seqnames

    def _match_pedigree_to_samples(self):
        vcf_samples = list()
        for vcf in self.vcfs:
            vcf_samples += vcf.samples
        vcf_samples = np.array(vcf_samples)

        vcf_samples_order = [list(vcf.samples) for vcf in self.vcfs]
        vcf_samples = set(vcf_samples)
        pedigree_samples = set(self.families.ped_df["sample_id"].values)
        missing_samples = vcf_samples.difference(pedigree_samples)

        vcf_samples = vcf_samples.difference(missing_samples)
        assert vcf_samples.issubset(pedigree_samples)

        seen = set()
        for person in self.families.persons.values():
            if person.sample_id in vcf_samples:
                if person.sample_id in seen:
                    continue
                for vcf_index, samples_order in enumerate(vcf_samples_order):
                    if person.sample_id in samples_order:
                        person.set_attr(
                            "sample_index",
                            (
                                vcf_index,
                                samples_order.index(person.sample_id)
                            )
                        )
                        seen.add(person.sample_id)
                        break
            else:
                person.set_attr("generated", True)
        self.families.redefine()

    def _build_family_alleles_indexes(self):
        vcf_offsets = [0] * len(self.vcfs)
        for vcf_index in range(1, len(self.vcfs)):
            vcf_offsets[vcf_index] = vcf_offsets[vcf_index - 1] + len(
                self.vcfs[vcf_index - 1].samples
            )

        self.families_allele_indexes = []

        for family in self.families.values():
            samples_indexes = []
            for vcf_index, sample_index in family.samples_index:
                offset = vcf_offsets[vcf_index]
                samples_indexes.append(sample_index + offset)
            samples_indexes = np.array(tuple(samples_indexes))
            allele_indexes = np.stack(
                [2 * samples_indexes, 2 * samples_indexes + 1]
            ).reshape([1, 2 * len(samples_indexes)], order="F")[0]

            self.families_allele_indexes.append(
                (family, allele_indexes)
            )

    def _build_independent_persons_indexes(self):
        self.independent = self.families.persons_without_parents()
        self.independent_indexes = []
        for person in self.independent:
            self.independent_indexes.append(person.sample_index)
        self.independent_indexes = np.array(tuple(self.independent_indexes))
        assert len(self.independent_indexes) == len(self.independent), (
            len(self.independent_indexes),
            len(self.independent),
        )

    # def _build_summary_variant(self, summary_index, vcf_variant):
    #     records = []
    #     allele_count = len(vcf_variant.ALT) + 1
    #     records.append(
    #         {
    #             "chrom": vcf_variant.CHROM,
    #             "position": vcf_variant.start + 1,
    #             "reference": vcf_variant.REF,
    #             "alternative": None,
    #             "summary_variant_index": summary_index,
    #             "allele_index": 0,
    #             "allele_count": allele_count,
    #         }
    #     )
    #     for allele_index, alt in enumerate(vcf_variant.ALT):
    #         records.append(
    #             {
    #                 "chrom": vcf_variant.CHROM,
    #                 "position": vcf_variant.start + 1,
    #                 "reference": vcf_variant.REF,
    #                 "alternative": alt,
    #                 "summary_variant_index": summary_index,
    #                 "allele_index": allele_index + 1,
    #                 "allele_count": allele_count,
    #             }
    #         )
    #     return SummaryVariantFactory.summary_variant_from_records(records)

    def _compare_vcf_variants_gt(self, lhs, rhs):
        """
        Returns true if left vcf variant position in file is
        larger than right vcf variant position in file
        """
        # TODO: Change this to use a dict
        if lhs is None:
            return True

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
        assert lhs is not None

        if rhs is None:
            return False
        return lhs.CHROM == rhs.CHROM and lhs.POS == rhs.POS

    def _find_current_vcf_variant(self, vcf_variants):
        assert len(vcf_variants)
        min_index = 0
        for index in range(1, len(vcf_variants)):
            if vcf_variants[index] is None:
                continue
            if self._compare_vcf_variants_gt(
                    vcf_variants[min_index], vcf_variants[index]):
                min_index = index
        return vcf_variants[min_index]

    def _calc_allele_frequencies(self, summary_variant, vcf_variants):
        result = [
            {
                "n_parents_called": 0,
                "n_alleles": [0] * summary_variant.allele_count,
            }
            for _ in vcf_variants
        ]

        for vcf_index, vcf in enumerate(vcf_variants):
            if vcf is None:
                continue

            sample_index = self.independent_indexes[
                self.independent_indexes[:, 0] == vcf_index, :][:, 1].T
            allele_index = np.stack(
                [2 * sample_index, 2 * sample_index + 1]).reshape(
                    [1, 2 * len(sample_index)], order="F")[0]

            current_vcf = self.vcfs[vcf_index]
            samples_count = len(current_vcf.samples)
            logger.debug(
                f"samples len: {samples_count}; "
                f"gt_idxs: {len(vcf.gt_idxs)}; "
                f"{set(vcf.gt_idxs)}")
            if len(vcf.gt_idxs) == samples_count and \
                    set(vcf.gt_idxs) == set([-1]):
                gt_idxs = -1 * np.ones(2 * samples_count, dtype = np.int)
            else:
                gt_idxs = vcf.gt_idxs

            vcf_gt = gt_idxs[allele_index]
            vcf_gt = vcf_gt.reshape([2, len(sample_index)], order="F")

            unknown = np.any(vcf_gt == -1, axis=0)
            vcf_gt = vcf_gt[:, np.logical_not(unknown)]
            result[vcf_index]["n_parents_called"] += vcf_gt.shape[1]

            for allele in summary_variant.alleles:
                allele_index = allele["allele_index"]
                matched_alleles = (vcf_gt == allele_index).astype(np.int32)
                result[vcf_index]["n_alleles"][allele_index] += np.sum(
                    matched_alleles
                )
        n_independent_parents = len(self.independent_indexes)
        n_parents_called = sum([r["n_parents_called"] for r in result])
        percent_parents_called = None

        for allele in summary_variant.alleles:
            if n_independent_parents > 0:
                percent_parents_called = (
                    100.0 * n_parents_called
                ) / n_independent_parents
            allele_index = allele["allele_index"]
            n_alleles = sum([r["n_alleles"][allele_index] for r in result])
            allele_freq = 0
            if n_parents_called > 0:
                allele_freq = (100.0 * n_alleles) / (2.0 * n_parents_called)
            freq = {
                "af_parents_called_count": int(n_parents_called),
                "af_parents_called_percent": float(percent_parents_called),
                "af_allele_count": int(n_alleles),
                "af_allele_freq": float(allele_freq),
            }
            allele.update_attributes(freq)

    def _full_variants_iterator_impl(self, initial_summary_variant_index=0):

        summary_variant_index = initial_summary_variant_index
        for region in self.regions:
            vcf_iterators = self._build_vcf_iterators(region)
            vcf_variants = [next(it, None) for it in vcf_iterators]

            while True:
                if all([vcf_variant is None for vcf_variant in vcf_variants]):
                    break

                current_vcf_variant = self._find_current_vcf_variant(
                    vcf_variants
                )
                current_summary_variant = \
                    SummaryVariantFactory.summary_variant_from_vcf(
                        current_vcf_variant, summary_variant_index)

                vcf_iterator_idexes_to_advance = list()
                vcf_gt_variants = list()
                for idx, vcf_variant in enumerate(vcf_variants):
                    if self._compare_vcf_variants_eq(
                        current_vcf_variant, vcf_variant
                    ):
                        vcf_gt_variants.append(vcf_variant)
                        vcf_iterator_idexes_to_advance.append(idx)
                    else:
                        vcf_gt_variants.append(None)
                self._calc_allele_frequencies(
                    current_summary_variant, vcf_gt_variants
                )
                family_genotypes = VcfFamiliesGenotypes(self, vcf_gt_variants)

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


class VcfLoader(VariantsGenotypesLoader):
    def __init__(
            self,
            families,
            vcf_files,
            genome: Genome,
            regions=None,
            params={},
            **kwargs):

        all_filenames, filenames = self._collect_filenames(params, vcf_files)

        super(VcfLoader, self).__init__(
            families=families,
            filenames=all_filenames,
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            expect_genotype=True,
            expect_best_state=False,
            params=params)

        self.set_attribute("source_type", "vcf")
        logger.debug(f"loader passed VCF files {vcf_files}")
        logger.debug(f"collected VCF files: {all_filenames}, {filenames}")

        self.vcf_files = vcf_files
        self.vcf_loaders = [
            SingleVcfLoader(
                families, vcf_files, genome, regions=regions, params=params)
            for vcf_files in filenames if vcf_files
        ]

    @classmethod
    def _arguments(cls):
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "vcf_files",
            value_type=str,
            nargs="+",
            metavar="<VCF filenames>",
            help_text="VCF files to import",
        ))
        arguments.append(CLIArgument(
            "--vcf-include-reference-genotypes",
            default_value=False,
            help_text="include reference only variants "
            "[default_value: %(default)s]",
            action="store_true",
        ))
        arguments.append(CLIArgument(
            "--vcf-include-unknown-family-genotypes",
            default_value=False,
            help_text="include family variants with fully unknown genotype "
            "[default: %(default)s]",
            action="store_true",
        ))
        arguments.append(CLIArgument(
            "--vcf-include-unknown-person-genotypes",
            default_value=False,
            help_text="include family variants with "
            "partially unknown genotype [default: %(default)s]",
            action="store_true",
        ))
        arguments.append(CLIArgument(
            "--vcf-multi-loader-fill-in-mode",
            default_value="reference",
            help_text="used for multi VCF files loader "
            "to fill missing genotypes; "
            "supported values are `reference` or `unknown`"
            "[default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--vcf-denovo-mode",
            default_value="possible_denovo",
            help_text="used for handling family variants "
            "with denovo inheritance; "
            "supported values are: `denovo`, `possible_denovo`, `ignore`; "
            "[default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--vcf-omission-mode",
            default_value="possible_omission",
            help_text="used for handling family variants with omission "
            "inheritance; "
            "supported values are: `omission`, `possible_omission`, `ignore`; "
            "[default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--vcf-chromosomes",
            value_type=str,
            help_text="specifies a list of filename template "
            "substitutions; then specified variant filename(s) are treated "
            "as templates and each occurent of `{vc}` is replaced "
            "consecutively by elements of VCF wildcards list; "
            "by default the list is empty and no substitution "
            "takes place. "
            "[default: None]",
        ))
        return arguments

    def _collect_filenames(self, params, vcf_files):
        if params.get("vcf_chromosomes", None):
            vcf_chromosomes = [
                wc.strip() for wc in params.get("vcf_chromosomes").split(";")
            ]

            glob_filenames = [
                [vcf_file.replace("[vc]", vc) for vcf_file in vcf_files]
                for vc in vcf_chromosomes
            ]

        else:
            glob_filenames = [vcf_files]

        logger.debug(f"collecting VCF filenames glob: {glob_filenames}")

        result = []
        for batches_globnames in glob_filenames:
            batches_result = []
            for globname in batches_globnames:

                filenames = glob.glob(globname)
                if len(filenames) == 0:
                    continue
                assert len(filenames) == 1, (globname, filenames)
                batches_result.append(filenames[0])
            result.append(batches_result)
        filenames = result
        all_filenames = list(itertools.chain.from_iterable(filenames))
        return all_filenames, filenames

    @property
    def variants_filenames(self):
        return self.vcf_files

    @property
    def chromosomes(self):
        assert len(self.vcf_loaders) > 0
        all_chromosomes = []
        for loader in self.vcf_loaders:
            for chrom in loader.chromosomes:
                if chrom not in all_chromosomes:
                    all_chromosomes.append(chrom)
        return all_chromosomes

    def reset_regions(self, regions):
        for single_loader in self.vcf_loaders:
            single_loader.reset_regions(regions)

    def _full_variants_iterator_impl(self):
        summary_index = 0
        for vcf_loader in self.vcf_loaders:
            iterator = vcf_loader._full_variants_iterator_impl(summary_index)
            try:
                for summary_variant, family_variants in iterator:
                    yield summary_variant, family_variants
                    summary_index += 1
            except StopIteration:
                pass

    @classmethod
    def parse_cli_arguments(cls, argv):
        super().parse_cli_arguments(argv, use_defaults=False)
        filenames = argv.vcf_files

        assert argv.vcf_multi_loader_fill_in_mode in set(
            ["reference", "unknown"]
        )
        assert argv.vcf_denovo_mode in set(
            ["denovo", "possible_denovo", "ignore"]
        ), argv.vcf_denovo_mode
        assert argv.vcf_omission_mode in set(
            ["omission", "possible_omission", "ignore"]
        ), argv.vcf_omission_mode
        params = {
            "vcf_include_reference_genotypes": str2bool(
                argv.vcf_include_reference_genotypes
            ),
            "vcf_include_unknown_family_genotypes": str2bool(
                argv.vcf_include_unknown_family_genotypes
            ),
            "vcf_include_unknown_person_genotypes": str2bool(
                argv.vcf_include_unknown_person_genotypes
            ),
            "vcf_multi_loader_fill_in_mode":
            argv.vcf_multi_loader_fill_in_mode,
            "vcf_denovo_mode": argv.vcf_denovo_mode,
            "vcf_omission_mode": argv.vcf_omission_mode,
            "vcf_chromosomes": argv.vcf_chromosomes,
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
        }
        return filenames, params
