import os
import itertools
import glob
import logging

from collections import Counter

import numpy as np

import pysam

from dae.utils.helpers import str2bool
from dae.genome.genome_access import GenomicSequenceBase

from dae.utils.variant_utils import is_all_reference_genotype, \
    is_all_unknown_genotype, \
    is_unknown_genotype

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
        self.known_independent_genotypes = None

    def full_families_genotypes(self):
        raise NotImplementedError()

    def get_family_best_state(self, family):
        raise NotImplementedError()

    def get_family_genotype(self, family):
        raise NotImplementedError()

    def family_genotype_iterator(self):
        self.known_independent_genotypes = []

        fill_value = self.loader._fill_missing_value
        samples_index = self.loader.samples_vcf_index

        for family in self.loader.families.values():

            gt = []
            for person in family.members_in_order:
                vcf_index = samples_index.get(person.sample_id)
                assert vcf_index is not None, (person, self.vcf_variants)

                vcf_variant = self.vcf_variants[vcf_index]
                if vcf_variant is None:
                    sample_genotype = (fill_value, fill_value)
                else:
                    sample_genotype = vcf_variant.samples.get(person.sample_id)
                    assert sample_genotype is not None, (
                        person, self.vcf_variants)

                    sample_genotype = sample_genotype["GT"]
                    if len(sample_genotype) == 1:
                        sample_genotype = (sample_genotype[0], -2)
                    assert len(sample_genotype) == 2, (
                        family, person, sample_genotype)
                    sample_genotype = tuple(map(
                        lambda g: g if g is not None else -1,
                        sample_genotype))
                gt.append(sample_genotype)
            if len(gt) == 0:
                continue

            gt = np.array(gt, np.int8)
            gt = gt.T
            assert len(gt.shape) == 2, (gt, family)
            assert gt.shape[0] == 2

            if is_unknown_genotype(gt):
                if not self.loader.include_unknown_person_genotypes:
                    continue
            else:
                for index, person in enumerate(family.members_in_order):
                    if person.person_id not in self.loader.independent_persons:
                        continue
                    self.known_independent_genotypes.append(
                        gt[:, index]
                    )

            if is_all_unknown_genotype(gt) and \
                    not self.loader.include_unknown_family_genotypes:
                continue

            if is_all_reference_genotype(gt) and \
                    not self.loader.include_reference_genotypes:
                continue

            yield family, gt, None


class SingleVcfLoader(VariantsGenotypesLoader):
    def __init__(
            self,
            families,
            vcf_files,
            genome: GenomicSequenceBase,
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
            logger.warning(
                "unexpected `vcf_multi_loader_fill_in_mode` value",
                f"{fill_in_mode}; "
                f"expected values are `reference` or `unknown`")
            self._fill_missing_value = 0

        self.fixed_pedigree = params.get("vcf_pedigree_mode", "fixed") == \
            "fixed"

        self._init_vcf_readers()
        self._match_pedigree_to_samples()

        self._build_samples_vcf_index()
        self.independent_persons = set([
            p.person_id for p in self.families.persons_without_parents()])

        # self._build_family_alleles_indexes()
        # self._build_independent_persons_indexes()
        self._init_chromosome_order()
        self._init_denovo_mode()
        self._init_omission_mode()

        self.include_reference_genotypes = str2bool(
            params.get("vcf_include_reference_genotypes", False))
        self.include_unknown_family_genotypes = str2bool(
            params.get("vcf_include_unknown_family_genotypes", False))
        self.include_unknown_person_genotypes = str2bool(
            params.get("vcf_include_unknown_person_genotypes", False))
        self.multi_loader_fill_in_mode = params.get(
            "vcf_multi_loader_fill_in_mode", "reference")

    def _init_denovo_mode(self):
        denovo_mode = self.params.get("vcf_denovo_mode", "possible_denovo")
        if denovo_mode == "possible_denovo":
            self._denovo_handler = self._possible_denovo_mode_handler
        elif denovo_mode == "denovo":
            self._denovo_handler = self._denovo_mode_handler
        elif denovo_mode == "ignore":
            self._denovo_handler = self._ignore_denovo_mode_handler
        else:
            logger.warning(
                f"unexpected denovo mode: {denovo_mode}; "
                f"using possible_denovo")
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
            logger.warning(
                f"unexpected omission mode: {omission_mode}; "
                f"using possible_omission")
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
        logger.debug(f"SingleVcfLoader input files: {self.filenames}")

        for file in self.filenames:
            self.vcfs.append(
                pysam.VariantFile(file))

    def _build_vcf_iterators(self, region):
        if region is None:
            return [
                vcf.fetch()
                for vcf in self.vcfs
            ]
        else:
            return [
                vcf.fetch(region=region)
                for vcf in self.vcfs]

    def _init_chromosome_order(self):
        seqnames = list(self.vcfs[0].header.contigs)
        if not all([
                list(vcf.header.contigs) == seqnames
                for vcf in self.vcfs]):
            logger.warning(
                f"VCF files {self.filenames} do not have the same list "
                f"of contigs")

        chrom_order = dict()
        for idx, seq in enumerate(seqnames):
            chrom_order[seq] = idx

        self.chrom_order = chrom_order

    @property
    def chromosomes(self):
        assert len(self.vcfs) > 0

        seqnames = list(self.vcfs[0].header.contigs)
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
            intersection = set(vcf_samples) & set(vcf.header.samples)
            if intersection:
                logger.warning(
                    f"vcf samples present in multiple batches: "
                    f"{intersection}")

            vcf_samples.extend(list(vcf.header.samples))

        logger.info(f"vcf samples (all): {len(vcf_samples)}")

        vcf_samples_order = [list(vcf.header.samples) for vcf in self.vcfs]
        vcf_samples = set(vcf_samples)
        logger.info(f"vcf samples (set): {len(vcf_samples)}")
        pedigree_samples = set(self.families.pedigree_samples())
        logger.info(f"pedigree samples (all): {len(pedigree_samples)}")

        missing_samples = vcf_samples.difference(pedigree_samples)
        if missing_samples:
            logger.info(
                f"vcf samples not found in pedigree: {len(missing_samples)}; "
                f"{missing_samples}")

        vcf_samples = vcf_samples.difference(missing_samples)
        assert vcf_samples.issubset(pedigree_samples)
        logger.info(f"vcf samples (matched): {len(vcf_samples)}")

        seen = set()
        not_sequenced = set()
        counters = Counter()
        for person in self.families.persons.values():
            if person.generated:
                counters["generated"] += 1
                continue

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
                        counters["found"] += 1
                        break
            elif not self.fixed_pedigree:
                if not person.generated and not person.not_sequenced:
                    not_sequenced.add(person.person_id)
                    person.set_attr("not_sequenced", True)
                    counters["not_sequenced"] += 1
                    logger.info(
                        f"person {person.person_id} marked as "
                        f"'not_sequenced'; ")
            else:
                if not person.missing:
                    logger.info(
                        f"person {person} marked as missing")

                    person.set_attr(
                        "sample_index",
                        (
                            None,
                            None
                        )
                    )
                    person.set_attr("missing", True)
                    counters["missing"] += 1
                counters["missing"] += 1

        logger.warning(f"people stats: {counters}")

        self.families.redefine()
        logger.warning(
            f"persons changed to not_sequenced {len(not_sequenced)} "
            f"in {self.filenames}")
        self.families_samples_indexes = [
            (family, family.samples_index)
            for family in self.families.values()
        ]

    def _build_samples_vcf_index(self):
        samples_index = {}
        vcf_samples = [
            set(vcf.header.samples)
            for vcf in self.vcfs]

        for person in self.families.real_persons.values():
            for index, samples in enumerate(vcf_samples):
                if person.sample_id in samples:
                    samples_index[person.sample_id] = index
                    break
        self.samples_vcf_index = samples_index

    # def _build_family_alleles_indexes(self):
    #     vcf_offsets = [0] * len(self.vcfs)
    #     for vcf_index in range(1, len(self.vcfs)):
    #         vcf_offsets[vcf_index] = vcf_offsets[vcf_index - 1] + len(
    #             self.vcfs[vcf_index - 1].samples
    #         )

    #     self.families_allele_indexes = []

    #     for family in self.families.values():
    #         samples_indexes = []
    #         for person in family.members_in_order:
    #             vcf_index, sample_index = person.sample_index
    #             if vcf_index is None or sample_index is None:
    #                 assert vcf_index is None and sample_index is None
    #                 continue
    #             offset = vcf_offsets[vcf_index]
    #             samples_indexes.append(sample_index + offset)
    #         samples_indexes = np.array(tuple(samples_indexes))
    #         allele_indexes = np.stack(
    #             [2 * samples_indexes, 2 * samples_indexes + 1]
    #         ).reshape([1, 2 * len(samples_indexes)], order="F")[0]

    #         self.families_allele_indexes.append(
    #             (family, allele_indexes)
    #         )

    # def _build_independent_persons_indexes(self):
    #     self.independent = self.families.persons_without_parents()
    #     self.independent_indexes = []

    #     logger.debug(f"independent persons: {len(self.independent)}")
    #     missing = 0
    #     for person in self.independent:
    #         if person.missing:
    #             logger.debug(
    #                 f"independent individual missing: "
    #                 f"{person}; {person.missing}"
    #             )
    #             missing += 1
    #             continue
    #         self.independent_indexes.append(person.sample_index)
    #     self.independent_indexes = np.array(tuple(self.independent_indexes))

    #     logger.debug(
    #         f"independent: found={len(self.independent_indexes)}; "
    #         f"missing={missing}")

    #     assert len(self.independent_indexes) + missing == \
    #         len(self.independent), (
    #             len(self.independent_indexes),
    #             missing,
    #             len(self.independent),
    #         )

    def _compare_vcf_variants_gt(self, lhs, rhs):
        """
        Returns true if left vcf variant position in file is
        larger than right vcf variant position in file
        """
        # TODO: Change this to use a dict
        if lhs is None:
            return True

        l_chrom_idx = self.chrom_order.get(lhs.chrom)
        r_chrom_idx = self.chrom_order.get(rhs.chrom)

        if l_chrom_idx > r_chrom_idx:
            return True
        elif lhs.pos > rhs.pos:
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
        return lhs.chrom == rhs.chrom and lhs.pos == rhs.pos

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

    def _calc_allele_frequencies(
            self, summary_variant, known_independent_genotypes):

        n_independent_parents = len(self.independent_persons)
        n_parents_called = 0
        if len(known_independent_genotypes) > 0:
            n_parents_called = known_independent_genotypes.shape[1]

        ref_n_alleles = 0
        ref_allele_freq = 0.0

        for allele in summary_variant.alleles:
            allele_index = allele["allele_index"]
            n_alleles = np.sum(known_independent_genotypes == allele_index)
            allele_freq = 0.0

            if n_independent_parents > 0:
                percent_parents_called = (
                    100.0 * n_parents_called
                ) / n_independent_parents
            if n_parents_called > 0:
                allele_freq = (100.0 * n_alleles) / (2.0 * n_parents_called)

            if allele_index == 0:
                ref_n_alleles = n_alleles
                ref_allele_freq = allele_freq

            freq = {
                "af_parents_called_count": int(n_parents_called),
                "af_parents_called_percent": float(percent_parents_called),
                "af_allele_count": int(n_alleles),
                "af_allele_freq": float(allele_freq),
                "af_ref_allele_count": int(ref_n_alleles),
                "af_ref_allele_freq": float(ref_allele_freq),
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
                        current_vcf_variant, summary_variant_index,
                        transmission_type=self.transmission_type)

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

                if len(current_summary_variant.alt_alleles) > 127:
                    logger.warning(
                        f"more than 127 alternative alleles; "
                        f"some alleles will be skipped: "
                        f"{current_summary_variant}")

                else:

                    assert len(current_summary_variant.alt_alleles) < 128, (
                        len(current_summary_variant.alt_alleles),
                        current_summary_variant
                    )

                    family_genotypes = VcfFamiliesGenotypes(
                        self, vcf_gt_variants)
                    family_variants = []

                    for fam, gt, bs in family_genotypes \
                            .family_genotype_iterator():

                        fv = FamilyVariant(
                            current_summary_variant, fam, gt, bs)
                        if self._denovo_handler(fv):
                            continue
                        if self._omission_handler(fv):
                            continue
                        family_variants.append(fv)

                    known_independent_genotypes = \
                        family_genotypes.known_independent_genotypes
                    assert known_independent_genotypes is not None

                    known_independent_genotypes = np.array(
                        known_independent_genotypes, np.int8).T

                    self._calc_allele_frequencies(
                        current_summary_variant,
                        known_independent_genotypes)

                    yield current_summary_variant, family_variants

                for idx in vcf_iterator_idexes_to_advance:
                    vcf_variants[idx] = next(vcf_iterators[idx], None)
                summary_variant_index += 1


class VcfLoader(VariantsGenotypesLoader):
    def __init__(
            self,
            families,
            vcf_files,
            genome: GenomicSequenceBase,
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
        self.vcf_loaders = []
        if vcf_files:
            for vcf_files_batch in filenames:
                if vcf_files_batch:
                    vcf_families = families.copy()
                    vcf_loader = SingleVcfLoader(
                        vcf_families, vcf_files_batch,
                        genome, regions=regions, params=params)
                    self.vcf_loaders.append(vcf_loader)

        pedigree_mode = params.get("vcf_pedigree_mode", "fixed")
        if pedigree_mode == "intersection":
            self.families = self._families_intersection()
        elif pedigree_mode == "union":
            self.families = self._families_union()

        logger.info(
            f"real persons/sample: {len(self.families.real_persons)}")
        for vcf_loader in self.vcf_loaders:
            vcf_families = vcf_loader.families
            logger.info(
                f"real persons/sample: {len(vcf_families.real_persons)} "
                f"in {vcf_loader.filenames}")

    def _families_intersection(self):
        logger.warning("families intersection run...")
        families = self.vcf_loaders[0].families
        for vcf_loader in self.vcf_loaders:
            other_families = vcf_loader.families
            assert len(families.persons) == len(other_families.persons)
            for other_person in other_families.persons.values():
                if other_person.not_sequenced:
                    person = families.persons[other_person.person_id]
                    logger.warning(
                        f"families intersection: person {person.person_id} "
                        f"is marked as 'not_sequenced'")
                    person.set_attr("not_sequenced", True)
        families.redefine()

        for vcf_loader in self.vcf_loaders:
            vcf_loader.families = families

        return families

    def _families_union(self):
        logger.warning("families union run...")
        families = self.vcf_loaders[0].families
        for person_id, person in families.persons.items():
            if not person.not_sequenced:
                continue
            for vcf_loader in self.vcf_loaders:
                other_person = vcf_loader.families.persons[person_id]

                if not other_person.not_sequenced:
                    logger.warning(
                        f"families union: person {person.person_id} "
                        f"'not_sequenced' flag changed to 'sequenced'")
                    person.set_attr("not_sequenced", False)
                    break

        families.redefine()

        for vcf_loader in self.vcf_loaders:
            vcf_loader.families = families

        return families

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
            default_value="ignore",
            help_text="used for handling family variants "
            "with denovo inheritance; "
            "supported values are: `denovo`, `possible_denovo`, `ignore`; "
            "[default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--vcf-omission-mode",
            default_value="ignore",
            help_text="used for handling family variants with omission "
            "inheritance; "
            "supported values are: `omission`, `possible_omission`, `ignore`; "
            "[default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--vcf-pedigree-mode",
            default_value="fixed",
            help_text="used for handling missmathes between samples in VCF"
            "and sample in pedigree file;"
            "supported values are: 'intersection', 'union', 'fixed';"
            "'fixed' mode means that pedigree should be accept 'as is' "
            "without any modifications; samples found in pedigree but not "
            "in the VCF should be patched with unknown genotype;"
            "[default: 'fixed']",
        ))
        arguments.append(CLIArgument(
            "--vcf-chromosomes",
            value_type=str,
            help_text="specifies a list of filename template "
            "substitutions; then specified variant filename(s) are treated "
            "as templates and each occurent of `[vc]` is replaced "
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
            if all(["[vc]" in vcf_file for vcf_file in vcf_files]):
                glob_filenames = [
                    [vcf_file.replace("[vc]", vc) for vcf_file in vcf_files]
                    for vc in vcf_chromosomes
                ]
            elif all(["[vc]" not in vcf_file for vcf_file in vcf_files]):
                logger.warning(
                    f"VCF files {vcf_files} does not contain '[vc]' pattern, "
                    f"but '--vcf-chromosomes' argument is passed; skipping...")
                glob_filenames = [vcf_files]
            else:
                logger.error(
                    f"some VCF files contain '[vc]' pattern, some not: "
                    f"{vcf_files}; can't continue...")
                raise ValueError(
                    f"some VCF files does not have '[vc]': {vcf_files}")
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
        assert argv.vcf_pedigree_mode in set(
            ["intersection", "union", "fixed"]
        ), argv.vcf_pedigree_mode

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
            "vcf_pedigree_mode": argv.vcf_pedigree_mode,
            "vcf_chromosomes": argv.vcf_chromosomes,
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
        }
        return filenames, params
