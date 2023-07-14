"""Defines variant loader classed for VCF variants."""

import itertools
import logging
from collections import Counter
from collections.abc import Callable
from typing import Set

from urllib.parse import urlparse
from fsspec.core import url_to_fs  # type: ignore

import numpy as np

import pysam  # type: ignore

from dae.utils.helpers import str2bool
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils import fs_utils

from dae.utils.variant_utils import is_all_reference_genotype, \
    is_all_unknown_genotype, \
    is_unknown_genotype

from dae.variants.attributes import Inheritance
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.variants_loaders.raw.loader import VariantsGenotypesLoader, \
    TransmissionType, \
    FamiliesGenotypes, \
    CLIArgument


logger = logging.getLogger(__name__)


class VcfFamiliesGenotypes(FamiliesGenotypes):
    """Class for family genotypes build vrom VCF variant."""

    def __init__(self, loader, vcf_variants):
        super().__init__()

        self.loader = loader
        self.vcf_variants = vcf_variants
        self.known_independent_genotypes = []

    def full_families_genotypes(self):
        raise NotImplementedError()

    def get_family_best_state(self, family):
        raise NotImplementedError()

    def get_family_genotype(self, family):
        raise NotImplementedError()

    def _collect_family_genotype(self, family, samples_index, fill_value):
        genotypes = []
        for person in family.members_in_order:
            vcf_index = samples_index.get(person.sample_id)
            assert vcf_index is not None, (person, self.vcf_variants)

            vcf_variant = self.vcf_variants[vcf_index]
            if vcf_variant is None:
                sample_genotype = (fill_value, fill_value)
            else:
                vcf_sample = vcf_variant.samples.get(person.sample_id)
                assert vcf_sample is not None, (person, self.vcf_variants)

                sample_genotype = vcf_sample["GT"]
                if len(sample_genotype) == 1:
                    sample_genotype = (sample_genotype[0], -2)
                assert len(sample_genotype) == 2, (
                    family, person, sample_genotype)
                sample_genotype = tuple(map(  # type: ignore
                    lambda g: g if g is not None else -1,
                    sample_genotype))
            genotypes.append(sample_genotype)
        return genotypes

    def _collect_known_independent_genotypes(self, family, genotype):
        for index, person in enumerate(family.members_in_order):
            if person.person_id not in self.loader.independent_persons:
                continue
            self.known_independent_genotypes.append(
                genotype[:, index]
            )

    def family_genotype_iterator(self):
        self.known_independent_genotypes = []
        # pylint: disable=protected-access
        fill_value = self.loader._fill_missing_value
        samples_index = self.loader.samples_vcf_index

        for family in self.loader.families.values():
            genotype = self._collect_family_genotype(
                family, samples_index, fill_value)

            if len(genotype) == 0:
                continue

            genotype = np.array(genotype, np.int8)
            genotype = genotype.T
            assert len(genotype.shape) == 2, (genotype, family)
            assert genotype.shape[0] == 2

            if is_unknown_genotype(genotype):
                if not self.loader.include_unknown_person_genotypes:
                    continue
            else:
                self._collect_known_independent_genotypes(family, genotype)

            if is_all_unknown_genotype(genotype) and \
                    not self.loader.include_unknown_family_genotypes:
                continue

            if is_all_reference_genotype(genotype) and \
                    not self.loader.include_reference_genotypes:
                continue

            yield family, genotype, None


class SingleVcfLoader(VariantsGenotypesLoader):
    """Defines a variant loader from single VCF file."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
            self,
            families,
            vcf_files,
            genome: ReferenceGenome,
            regions=None,
            params=None,
            **_kwargs):
        params = params if params else {}
        super().__init__(
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
            self._fill_missing_value: int = 0
        elif fill_in_mode == "unknown":
            self._fill_missing_value = -1
        else:
            logger.warning(
                "unexpected `vcf_multi_loader_fill_in_mode` value%s; "
                "expected values are `reference` or `unknown`", fill_in_mode)
            self._fill_missing_value = 0

        self.fixed_pedigree = params.get("vcf_pedigree_mode", "fixed") == \
            "fixed"

        self._init_vcf_readers()
        self._match_pedigree_to_samples()

        self._build_samples_vcf_index()
        self.independent_persons = set(
            p.person_id for p in self.families.persons_without_parents())

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
        self._denovo_handler: Callable[[FamilyVariant], bool]
        if denovo_mode == "possible_denovo":
            self._denovo_handler = self._possible_denovo_mode_handler
        elif denovo_mode == "denovo":
            self._denovo_handler = self._denovo_mode_handler
        elif denovo_mode == "ignore":
            self._denovo_handler = self._ignore_denovo_mode_handler
        else:
            logger.warning(
                "unexpected denovo mode: %s; "
                "using possible_denovo", denovo_mode)
            self._denovo_handler = self._possible_denovo_mode_handler

    @staticmethod
    def _possible_denovo_mode_handler(family_variant: FamilyVariant) -> bool:
        for fallele in family_variant.alleles:
            inheritance_in_members = fallele.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.denovo
                else Inheritance.possible_denovo
                for inh in inheritance_in_members
            ]
            # pylint: disable=protected-access
            fallele._inheritance_in_members = inheritance_in_members
        return False

    @staticmethod
    def _ignore_denovo_mode_handler(family_variant: FamilyVariant) -> bool:
        for fallele in family_variant.alleles:
            if Inheritance.denovo in fallele.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _denovo_mode_handler(_family_vairant: FamilyVariant) -> bool:
        return False

    def _init_omission_mode(self):
        omission_mode = self.params.get(
            "vcf_omission_mode", "possible_omission"
        )
        self._omission_handler: Callable[[FamilyVariant], bool]
        if omission_mode == "possible_omission":
            self._omission_handler = self._possible_omission_mode_handler
        elif omission_mode == "omission":
            self._omission_handler = self._omission_mode_handler
        elif omission_mode == "ignore":
            self._omission_handler = self._ignore_omission_mode_handler
        else:
            logger.warning(
                "unexpected omission mode: %s; "
                "using possible_omission", omission_mode)
            self._omission_handler = self._possible_omission_mode_handler

    @staticmethod
    def _possible_omission_mode_handler(family_variant: FamilyVariant) -> bool:
        for fallele in family_variant.alleles:
            inheritance_in_members = fallele.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.omission
                else Inheritance.possible_omission
                for inh in inheritance_in_members
            ]
            # pylint: disable=protected-access
            fallele._inheritance_in_members = inheritance_in_members
        return False

    @staticmethod
    def _ignore_omission_mode_handler(family_variant: FamilyVariant) -> bool:
        for fallele in family_variant.alleles:
            if Inheritance.omission in fallele.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _omission_mode_handler(_family_vairant: FamilyVariant) -> bool:
        return False

    def close(self):
        for vcf in self.vcfs:
            vcf.close()

    def _init_vcf_readers(self):
        self.vcfs = []
        logger.debug("SingleVcfLoader input files: %s", self.filenames)

        for file in self.filenames:
            # pylint: disable=no-member
            index_filename = fs_utils.tabix_index_filename(file)
            if index_filename is not None:
                index_filename = fs_utils.sign(index_filename
                                               )
            self.vcfs.append(
                pysam.VariantFile(
                    fs_utils.sign(file),
                    index_filename=index_filename)
            )

    def _build_vcf_iterators(self, region):
        if region is None:
            return [
                vcf.fetch()
                for vcf in self.vcfs
            ]
        return [
            vcf.fetch(region=self._unadjust_chrom_prefix(region))
            for vcf in self.vcfs]

    def _init_chromosome_order(self):
        seqnames = list(self.vcfs[0].header.contigs)
        if not all(
                list(vcf.header.contigs) == seqnames
                for vcf in self.vcfs):
            logger.warning(
                "VCF files %s do not have the same list "
                "of contigs", self.filenames)

        chrom_order = {}
        for idx, seq in enumerate(seqnames):
            chrom_order[seq] = idx

        self.chrom_order = chrom_order

    @property
    def chromosomes(self):
        """Return list of all chromosomes from VCF file(s)."""
        assert len(self.vcfs) > 0

        seqnames = list(self.vcfs[0].header.contigs)
        filename = self.filenames[0]
        tabix_index_filename = fs_utils.tabix_index_filename(filename)
        if tabix_index_filename is None:
            res = seqnames

        try:
            # pylint: disable=no-member
            index_filename = fs_utils.tabix_index_filename(filename)
            if index_filename is not None:
                index_filename = fs_utils.sign(index_filename)
            with pysam.Tabixfile(
                fs_utils.sign(filename),
                index=index_filename
            ) as tbx:
                res = list(tbx.contigs)
        except Exception:  # pylint: disable=broad-except
            res = seqnames

        return [self._adjust_chrom_prefix(chrom) for chrom in res]

    def _match_pedigree_to_samples(self):
        # pylint: disable=too-many-branches
        vcf_samples: Set[str] = set()
        for vcf in self.vcfs:
            intersection = set(vcf_samples) & set(vcf.header.samples)
            if intersection:
                logger.warning(
                    "vcf samples present in multiple batches: %s",
                    intersection)

            vcf_samples.update(list(vcf.header.samples))

        logger.info("vcf samples (all): %s", len(vcf_samples))

        vcf_samples_order = [list(vcf.header.samples) for vcf in self.vcfs]
        vcf_samples = set(vcf_samples)
        logger.info("vcf samples (set): %s", len(vcf_samples))
        pedigree_samples = set(self.families.pedigree_samples())
        logger.info("pedigree samples (all): %s", len(pedigree_samples))

        missing_samples = vcf_samples.difference(pedigree_samples)
        if missing_samples:
            logger.info(
                "vcf samples not found in pedigree: %s; %s",
                len(missing_samples), missing_samples)

        vcf_samples = vcf_samples.difference(missing_samples)
        assert vcf_samples.issubset(pedigree_samples)
        logger.info("vcf samples (matched): %s", len(vcf_samples))

        seen = set()
        not_sequenced = set()
        counters: Counter = Counter()
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
                        "person %s marked as "
                        "'not_sequenced';", person.person_id)
            else:
                if not person.missing:
                    logger.info(
                        "person %s marked as missing", person)

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

        logger.info("people stats: %s", counters)

        self.families.redefine()
        logger.info(
            "persons changed to not_sequenced %s in %s",
            len(not_sequenced), self.filenames)
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

    def _compare_vcf_variants_gt(self, lhs, rhs):
        """Compare two VCF variant positions.

        Returns true if left vcf variant position in file is
        larger than right vcf variant position in file.
        """
        # TODO: Change this to use a dict
        if lhs is None:
            return True

        l_chrom_idx = self.chrom_order.get(lhs.chrom)
        r_chrom_idx = self.chrom_order.get(rhs.chrom)
        assert l_chrom_idx is not None
        assert r_chrom_idx is not None

        if l_chrom_idx > r_chrom_idx:
            return True
        if lhs.pos > rhs.pos:
            return True
        return False

    @staticmethod
    def _compare_vcf_variants_eq(lhs, rhs):
        """Compare two VCF variant positions.

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

            percent_parents_called = 0.0

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
                if all(vcf_variant is None for vcf_variant in vcf_variants):
                    break

                current_vcf_variant = self._find_current_vcf_variant(
                    vcf_variants
                )
                current_summary_variant = \
                    SummaryVariantFactory.summary_variant_from_vcf(
                        current_vcf_variant, summary_variant_index,
                        transmission_type=self.transmission_type)

                vcf_iterator_idexes_to_advance = []
                vcf_gt_variants = []
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
                        "more than 127 alternative alleles; "
                        "some alleles will be skipped: %s",
                        current_summary_variant)

                else:

                    assert len(current_summary_variant.alt_alleles) < 128, (
                        len(current_summary_variant.alt_alleles),
                        current_summary_variant
                    )

                    family_genotypes = VcfFamiliesGenotypes(
                        self, vcf_gt_variants)
                    family_variants = []

                    for fam, genotype, best_state in family_genotypes \
                            .family_genotype_iterator():

                        fvariant = FamilyVariant(
                            current_summary_variant, fam, genotype, best_state)
                        if self._denovo_handler(fvariant):
                            continue
                        if self._omission_handler(fvariant):
                            continue
                        family_variants.append(fvariant)

                    known_independent_genotypes = \
                        family_genotypes.known_independent_genotypes
                    assert known_independent_genotypes is not None

                    independent_genotypes = np.array(
                        known_independent_genotypes, np.int8).T

                    self._calc_allele_frequencies(
                        current_summary_variant,
                        independent_genotypes)

                    yield current_summary_variant, family_variants

                for idx in vcf_iterator_idexes_to_advance:
                    vcf_variants[idx] = next(vcf_iterators[idx], None)
                summary_variant_index += 1


class VcfLoader(VariantsGenotypesLoader):
    """Defines variant loader for VCF variants."""

    def __init__(
            self,
            families,
            vcf_files,
            genome: ReferenceGenome,
            regions=None,
            params=None,
            **_kwargs):
        params = params if params else {}
        all_filenames, filenames = self._collect_filenames(params, vcf_files)

        super().__init__(
            families=families,
            filenames=all_filenames,
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            expect_genotype=True,
            expect_best_state=False,
            params=params)

        self.set_attribute("source_type", "vcf")
        logger.debug("loader passed VCF files %s", vcf_files)
        logger.debug("collected VCF files: %s, %s", all_filenames, filenames)

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
            "real persons/sample: %s", len(self.families.real_persons))
        for vcf_loader in self.vcf_loaders:
            vcf_families = vcf_loader.families
            logger.info(
                "real persons/sample: %s in %s",
                len(vcf_families.real_persons), vcf_loader.filenames)

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
                        "families intersection: person %s "
                        "is marked as 'not_sequenced'", person.person_id)
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
                        "families union: person %s "
                        "'not_sequenced' flag changed to 'sequenced'",
                        person.person_id)
                    person.set_attr("not_sequenced", False)
                    break

        families.redefine()

        for vcf_loader in self.vcf_loaders:
            vcf_loader.families = families

        return families

    def close(self):
        for vcf_loader in self.vcf_loaders:
            vcf_loader.close()

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

    @staticmethod
    def _glob(globname):

        filesystem, _ = url_to_fs(globname)
        filenames = filesystem.glob(globname)
        # fs.glob strips the protocol at the beginning. We need to add it back
        # otherwise there is no way to know the correct fs down the pipeline
        scheme = urlparse(globname).scheme
        if scheme:
            filenames = [f"{scheme}://{fn}" for fn in filenames]

        return filenames

    @staticmethod
    def _collect_filenames(params, vcf_files):
        if params.get("vcf_chromosomes", None):
            vcf_chromosomes = [
                wc.strip() for wc in params.get("vcf_chromosomes").split(";")
            ]
            if all("[vc]" in vcf_file for vcf_file in vcf_files):
                glob_filenames = [
                    [vcf_file.replace("[vc]", vc) for vcf_file in vcf_files]
                    for vc in vcf_chromosomes
                ]
            elif all("[vc]" not in vcf_file for vcf_file in vcf_files):
                logger.warning(
                    "VCF files %s does not contain '[vc]' pattern, "
                    "but '--vcf-chromosomes' argument is passed; skipping...",
                    vcf_files)
                glob_filenames = [vcf_files]
            else:
                logger.error(
                    "some VCF files contain '[vc]' pattern, some not: "
                    "%s; can't continue...", vcf_files)
                raise ValueError(
                    f"some VCF files does not have '[vc]': {vcf_files}")
        else:
            glob_filenames = [vcf_files]

        logger.debug("collecting VCF filenames glob: %s", glob_filenames)

        result = []
        for batches_globnames in glob_filenames:
            batches_result = []
            for globname in batches_globnames:
                filenames = VcfLoader._glob(globname)
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
        """Return list of all chromosomes from VCF files."""
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
            # pylint: disable=protected-access
            iterator = vcf_loader._full_variants_iterator_impl(summary_index)
            try:
                for summary_variant, family_variants in iterator:
                    yield summary_variant, family_variants
                    summary_index += 1
            except StopIteration:
                pass

    @classmethod
    def parse_cli_arguments(cls, argv, use_defaults=False):
        super().parse_cli_arguments(argv, use_defaults=use_defaults)
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
