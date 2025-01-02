"""Defines variant loader classed for VCF variants."""
from __future__ import annotations

import argparse
import itertools
import logging
from collections import Counter
from collections.abc import Callable, Generator, Iterator, Sequence
from typing import Any, cast
from urllib.parse import urlparse

import numpy as np
import pysam
from fsspec.core import url_to_fs

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Family
from dae.utils import fs_utils
from dae.utils.helpers import str2bool
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants_loaders.raw.loader import (
    CLIArgument,
    FamiliesGenotypes,
    TransmissionType,
    VariantsGenotypesLoader,
)

logger = logging.getLogger(__name__)


def vcffile_chromosomes(filename: str) -> list[str]:
    """Return list of all chromosomes from VCF file."""
    seqnames = []
    with pysam.VariantFile(filename) as vcf:
        seqnames = [str(c) for c in vcf.header.contigs]

    tabix_index_filename = fs_utils.tabix_index_filename(filename)
    if tabix_index_filename is None:
        return seqnames

    try:
        # pylint: disable=no-member
        assert tabix_index_filename is not None
        tabix_index_filename = fs_utils.sign(tabix_index_filename)
        with pysam.Tabixfile(
            fs_utils.sign(filename),
            index=tabix_index_filename,
        ) as tbx:
            return list(tbx.contigs)
    except Exception:  # noqa: BLE001
        return seqnames


class VcfFamiliesGenotypes(FamiliesGenotypes):
    """Class for family genotypes build vrom VCF variant."""

    def __init__(
        self, loader: SingleVcfLoader,
        all_genotypes: dict[str, tuple[int, ...]],
    ):
        super().__init__()
        self.loader = loader
        self.all_genotypes = all_genotypes
        self.known_independent_genotypes: list[tuple[int, int]] = []

    def _collect_family_genotype(
        self, family: Family,
        fill_value: int,
    ) -> tuple[
            list[tuple[int, int]],
            list[tuple[int, int]],
            tuple[bool, bool, bool],
        ]:
        genotypes: list[tuple[int, int]] = []
        independent_genotypes: list[tuple[int, int]] = []
        all_reference = True
        all_unknown = True
        has_unknown = False

        for person in family.members_in_order:
            sg: tuple[int, int] = cast(
                tuple[int, int],
                self.all_genotypes.get(person.sample_id) or
                (fill_value, fill_value))
            if len(sg) == 1:
                sg = (sg[0], -2)
            assert len(sg) == 2, (
                family, person, sg)
            sg = (
                sg[0] if sg[0] is not None else -1,
                sg[1] if sg[1] is not None else -1,
            )
            if sg != (0, 0):
                all_reference = False
            if sg != (-1, -1):
                all_unknown = False
            if sg[0] == -1 or sg[1] == -1:
                has_unknown = True

            genotypes.append(sg)
            if person.person_id in self.loader.independent_persons:
                independent_genotypes.append(sg)
        return (
            genotypes,
            independent_genotypes,
            (all_reference, all_unknown, has_unknown))

    def family_genotype_iterator(
        self,
    ) -> Generator[
            tuple[Family, np.ndarray, np.ndarray | None], None, None]:
        self.known_independent_genotypes = []
        # pylint: disable=protected-access
        fill_value = self.loader._fill_missing_value  # noqa: SLF001

        for family in self.loader.families.values():
            family_genotype, independent_genotypes, gt_type = \
                self._collect_family_genotype(family, fill_value)

            if len(family_genotype) == 0:
                continue

            genotype = np.array(family_genotype, np.int8)
            genotype = genotype.T
            assert len(genotype.shape) == 2, (genotype, family)
            assert genotype.shape[0] == 2
            all_reference, all_unknown, has_unknown = gt_type
            if has_unknown:
                if not self.loader.include_unknown_person_genotypes:
                    continue
            else:
                self.known_independent_genotypes.extend(independent_genotypes)

            if all_unknown and \
                    not self.loader.include_unknown_family_genotypes:
                continue

            if all_reference and \
                    not self.loader.include_reference_genotypes:
                continue

            yield family, genotype, None


class SingleVcfLoader(VariantsGenotypesLoader):
    """Defines a variant loader from single VCF file."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
            self,
            families: FamiliesData,
            vcf_files: list[str],
            genome: ReferenceGenome,
            regions: list[Region] | None = None,
            params: dict[str, Any] | None = None,
            **_kwargs: Any):
        params = params or {}
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

        fill_in_mode = params.get("vcf_multi_loader_fill_in_mode", "unknown")
        if fill_in_mode == "reference":
            self._fill_missing_value: int = 0
        elif fill_in_mode == "unknown":
            self._fill_missing_value = -1
        else:
            logger.warning(
                "unexpected `vcf_multi_loader_fill_in_mode` value%s; "
                "expected values are `reference` or `unknown`", fill_in_mode)
            self._fill_missing_value = -1

        self.fixed_pedigree = params.get("vcf_pedigree_mode", "fixed") == \
            "fixed"

        self._init_vcf_readers()
        self._match_pedigree_to_samples()

        self.independent_persons = {
            p.person_id for p in self.families.persons_without_parents()
        }

        self._init_chromosome_order()
        self._init_denovo_mode()
        self._init_omission_mode()

        self.include_reference_genotypes = str2bool(
            params.get("vcf_include_reference_genotypes", False))
        self.include_unknown_family_genotypes = str2bool(
            params.get("vcf_include_unknown_family_genotypes", False))
        self.include_unknown_person_genotypes = str2bool(
            params.get("vcf_include_unknown_person_genotypes", False))

    def _init_denovo_mode(self) -> None:
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
        for fa in family_variant.alleles:
            assert isinstance(fa, FamilyAllele)
            inheritance_in_members = fa.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.denovo
                else Inheritance.possible_denovo
                for inh in inheritance_in_members
            ]
            # pylint: disable=protected-access
            fa._inheritance_in_members = inheritance_in_members  # noqa: SLF001
        return False

    @staticmethod
    def _ignore_denovo_mode_handler(family_variant: FamilyVariant) -> bool:
        for fallele in family_variant.alleles:
            assert isinstance(fallele, FamilyAllele)
            if Inheritance.denovo in fallele.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _denovo_mode_handler(_family_vairant: FamilyVariant) -> bool:
        return False

    def _init_omission_mode(self) -> None:
        omission_mode = self.params.get(
            "vcf_omission_mode", "possible_omission",
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
        for fa in family_variant.alleles:
            assert isinstance(fa, FamilyAllele)
            inheritance_in_members = fa.inheritance_in_members
            inheritance_in_members = [
                inh
                if inh != Inheritance.omission
                else Inheritance.possible_omission
                for inh in inheritance_in_members
            ]
            # pylint: disable=protected-access
            fa._inheritance_in_members = inheritance_in_members  # noqa: SLF001
        return False

    @staticmethod
    def _ignore_omission_mode_handler(family_variant: FamilyVariant) -> bool:
        for fallele in family_variant.alleles:
            assert isinstance(fallele, FamilyAllele)
            if Inheritance.omission in fallele.inheritance_in_members:
                return True
        return False

    @staticmethod
    def _omission_mode_handler(_family_vairant: FamilyVariant) -> bool:
        return False

    def close(self) -> None:
        for vcf in self.vcfs:
            vcf.close()

    def _init_vcf_readers(self) -> None:
        self.vcfs: list[pysam.VariantFile] = []
        logger.debug("SingleVcfLoader input files: %s", self.filenames)

        for file in self.filenames:
            # pylint: disable=no-member
            index_filename = fs_utils.tabix_index_filename(file)
            if index_filename is not None:
                index_filename = fs_utils.sign(index_filename,
                                               )
            self.vcfs.append(
                pysam.VariantFile(
                    fs_utils.sign(file),
                    index_filename=index_filename),
            )

    def _build_vcf_iterators(
        self, region: Region | None,
    ) -> list[Iterator[pysam.VariantRecord]]:
        if region is None:
            return [
                vcf.fetch()
                for vcf in self.vcfs
            ]

        return [
            vcf.fetch(region=self._unadjust_chrom_prefix(str(region)))
            for vcf in self.vcfs]

    def _init_chromosome_order(self) -> None:
        seqnames = list(self.vcfs[0].header.contigs)
        if not all(
                list(vcf.header.contigs) == seqnames
                for vcf in self.vcfs):
            logger.warning(
                "VCF files %s do not have the same list "
                "of contigs", self.filenames)

        chrom_order = {
            seq: ids
            for ids, seq in enumerate(seqnames)
        }

        self.chrom_order = chrom_order

    @property
    def chromosomes(self) -> list[str]:
        """Return list of all chromosomes from VCF file(s)."""
        assert len(self.vcfs) > 0

        seqnames = [str(c) for c in self.vcfs[0].header.contigs]
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
                index=index_filename,
            ) as tbx:
                res = [str(c) for c in tbx.contigs]
        except Exception:  # noqa: BLE001
            res = seqnames

        return [self._adjust_chrom_prefix(chrom) for chrom in res]

    def _match_pedigree_to_samples(self) -> None:
        # pylint: disable=too-many-branches
        vcf_samples: set[str] = set()
        for vcf in self.vcfs:
            intersection = set(vcf_samples) & set(vcf.header.samples)
            if intersection:
                logger.warning(
                    "vcf samples present in multiple batches: %s",
                    intersection)

            vcf_samples.update(list(vcf.header.samples))

        logger.info("vcf samples (all): %s", len(vcf_samples))

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

        not_sequenced = set()
        counters: Counter = Counter()
        for person in self.families.persons.values():
            if person.generated:
                counters["generated"] += 1
                continue

            if person.sample_id in vcf_samples:
                continue
            if self.fixed_pedigree and not person.not_sequenced:
                counters["missing"] += 1
            else:
                if not person.generated and not person.not_sequenced:
                    not_sequenced.add(person.person_id)
                    person.set_attr("not_sequenced", value=True)
                    counters["not_sequenced"] += 1
                    logger.info(
                        "person %s marked as "
                        "'not_sequenced';", person.person_id)

        logger.info("people stats: %s", counters)

        if not_sequenced:
            logger.info(
                "persons changed to not_sequenced %s in %s",
                len(not_sequenced), self.filenames)
            self.families.redefine()

    def _compare_vcf_variants_gt(
        self, lhs: pysam.VariantRecord | None,
        rhs: pysam.VariantRecord | None,
    ) -> bool:
        """Compare two VCF variant positions.

        Returns true if left vcf variant position in file is
        larger than right vcf variant position in file.
        """
        if lhs is None:
            return True
        if rhs is None:
            return False
        l_chrom_idx = self.chrom_order.get(lhs.chrom)
        r_chrom_idx = self.chrom_order.get(rhs.chrom)
        assert l_chrom_idx is not None
        assert r_chrom_idx is not None

        if l_chrom_idx > r_chrom_idx:
            return True
        return lhs.pos > rhs.pos

    @staticmethod
    def _compare_vcf_variants_eq(
        lhs: pysam.VariantRecord,
        rhs: pysam.VariantRecord | None,
    ) -> bool:
        """Compare two VCF variant positions.

        Returns true if left vcf variant position in file is
        equal to right vcf variant position in file
        """
        assert lhs is not None
        if rhs is None:
            return False
        return lhs.chrom == rhs.chrom and lhs.pos == rhs.pos

    def _find_current_vcf_variant(
        self, vcf_variants: list[pysam.VariantRecord | None],
    ) -> pysam.VariantRecord | None:
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
            self, summary_variant: SummaryVariant,
            known_independent_genotypes: np.ndarray,
    ) -> None:
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

    def _full_variants_iterator_impl(
        self, initial_summary_index: int = 0,
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:

        summary_index = initial_summary_index
        for region in self.regions:
            if region is not None and "HLA" in region.chrom:
                logger.warning("skipping odd chromosomal region: %s", region)
                continue

            vcf_iterators = self._build_vcf_iterators(region)
            vcf_variants = [next(it, None) for it in vcf_iterators]

            while True:
                if all(vcf_variant is None for vcf_variant in vcf_variants):
                    break

                current_vcf_variant = self._find_current_vcf_variant(
                    vcf_variants,
                )
                assert current_vcf_variant is not None
                current_summary_variant = \
                    SummaryVariantFactory.summary_variant_from_vcf(
                        current_vcf_variant, summary_index,
                        transmission_type=self.transmission_type)

                all_genotypes, vcf_iterator_idexes_to_advance = \
                    self._collect_all_genotypes(
                        current_vcf_variant,
                        vcf_variants)

                if len(current_summary_variant.alt_alleles) > 127:
                    logger.warning(
                        "more than 127 alternative alleles; "
                        "some alleles will be skipped: %s",
                        current_summary_variant)

                family_genotypes = VcfFamiliesGenotypes(
                    self, all_genotypes)
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
                summary_index += 1

    def _collect_all_genotypes(
            self,
            current_vcf_variant: pysam.VariantRecord,
            vcf_variants: list[pysam.VariantRecord | None],
    ) -> tuple[dict[str, tuple[int, ...]], list[int]]:
        all_genotypes: dict[str, tuple[int, ...]] = {}
        vcf_iterator_idexes_to_advance: list[int] = []
        for idx, vcf_variant in enumerate(vcf_variants):
            if self._compare_vcf_variants_eq(
                        current_vcf_variant, vcf_variant,
                    ):
                vcf_iterator_idexes_to_advance.append(idx)
                assert vcf_variant is not None
                for sample_id in vcf_variant.header.samples:
                    if sample_id in all_genotypes:
                        logger.debug(
                                    "sample %s already in genotypes; skipping",
                                    sample_id)
                        continue
                    gt = vcf_variant.samples.get(sample_id)["GT"]
                    all_genotypes[sample_id] = gt
        return all_genotypes, vcf_iterator_idexes_to_advance


class VcfLoader(VariantsGenotypesLoader):
    """Defines variant loader for VCF variants."""

    def __init__(
        self,
        families: FamiliesData,
        vcf_files: list[str],
        genome: ReferenceGenome,
        regions: list[Region] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ARG002
    ):
        # pylint: disable=unused-argument
        params = params or {}
        all_filenames, filenames = self._collect_filenames(params, vcf_files)

        super().__init__(
            families=families,
            filenames=all_filenames,
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            regions=regions,
            expect_genotype=True,
            expect_best_state=False,
            params=params)

        self.set_attribute("source_type", "vcf")
        logger.debug("loader passed VCF files %s", vcf_files)
        logger.debug("collected VCF files: %s, %s", all_filenames, filenames)

        assert vcf_files

        self.vcf_files = vcf_files
        self.files_batches = filenames
        self.fixed_pedigree = params.get("vcf_pedigree_mode", "fixed") == \
            "fixed"

        self.vcf_loaders: list[SingleVcfLoader] | None = None

    def _filter_files_batches(
        self,
        files_batches: list[list[str]],
        regions: Sequence[Region | None],
    ) -> list[list[str]]:
        if regions == [None]:
            return files_batches
        result: list[list[str]] = []
        region_chromosomes = {r.chrom for r in regions if r is not None}
        for batch in files_batches:
            for filename in batch:
                chromosomes = {
                    self._adjust_chrom_prefix(c)
                    for c in vcffile_chromosomes(filename)
                }
                if set(chromosomes).intersection(region_chromosomes):
                    result.append(batch)
                    break
        return result

    def init_vcf_loaders(
        self,
    ) -> None:
        """Initialize VCF loaders."""
        self.vcf_loaders = []
        files_batches = self._filter_files_batches(
            self.files_batches,
            self.regions,
        )
        if len(files_batches) == 0:
            logger.warning(
                "no VCF files found for regions %s", self.regions)
            return
        if len(files_batches) == 1 and len(files_batches[0]) == 1:
            vcf_loader = SingleVcfLoader(
                self.families, files_batches[0],
                self.genome,
                params=self.params)
            vcf_loader.reset_regions(self.regions)
            self.vcf_loaders.append(vcf_loader)
            return

        for vcf_files_batch in files_batches:
            if vcf_files_batch:
                if self.fixed_pedigree:
                    vcf_families = self.families
                else:
                    vcf_families = self.families.copy()
                vcf_loader = SingleVcfLoader(
                    vcf_families, vcf_files_batch,
                    self.genome,
                    params=self.params)
                vcf_loader.reset_regions(self.regions)
                self.vcf_loaders.append(vcf_loader)

        pedigree_mode = self.params.get("vcf_pedigree_mode", "fixed")
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

    def _families_intersection(self) -> FamiliesData:
        assert self.vcf_loaders is not None
        if len(self.vcf_loaders) == 1:
            return self.vcf_loaders[0].families

        logger.warning("families intersection run...")
        families = self.vcf_loaders[0].families
        for vcf_loader in self.vcf_loaders:
            other_families = vcf_loader.families
            assert len(families.persons) == len(other_families.persons)
            for other_person in other_families.persons.values():
                if other_person.not_sequenced:
                    person = families.persons[other_person.fpid]
                    logger.warning(
                        "families intersection: person %s "
                        "is marked as 'not_sequenced'", person.person_id)
                    person.set_attr("not_sequenced", value=True)
        families.redefine()

        for vcf_loader in self.vcf_loaders:
            vcf_loader.families = families

        return families

    def _families_union(self) -> FamiliesData:
        assert self.vcf_loaders is not None
        if len(self.vcf_loaders) == 1:
            return self.vcf_loaders[0].families

        logger.warning("families union run...")
        families = self.vcf_loaders[0].families
        for fpid, person in families.persons.items():
            if not person.not_sequenced:
                continue
            for vcf_loader in self.vcf_loaders:
                other_person = vcf_loader.families.persons[fpid]

                if not other_person.not_sequenced:
                    logger.warning(
                        "families union: person %s "
                        "'not_sequenced' flag changed to 'sequenced'",
                        person.person_id)
                    person.set_attr("not_sequenced", value=False)
                    break

        families.redefine()

        for vcf_loader in self.vcf_loaders:
            vcf_loader.families = families

        return families

    def close(self) -> None:
        if self.vcf_loaders is None:
            return
        for vcf_loader in self.vcf_loaders:
            vcf_loader.close()

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
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
            default_value="unknown",
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
    def _glob(globname: str) -> list[str]:

        filesystem, _ = url_to_fs(globname)
        filenames = filesystem.glob(globname)
        # fs.glob strips the protocol at the beginning. We need to add it back
        # otherwise there is no way to know the correct fs down the pipeline
        scheme = urlparse(globname).scheme
        if scheme:
            filenames = [f"{scheme}://{fn}" for fn in filenames]

        return cast(list[str], filenames)

    @staticmethod
    def _collect_filenames(
        params: dict[str, Any], vcf_files: list[str],
    ) -> tuple[list[str], list[list[str]]]:
        if params.get("vcf_chromosomes"):
            vcf_chromosomes = [
                wc.strip() for wc in params["vcf_chromosomes"].split(";")
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

        result: list[list[str]] = []
        for batches_globnames in glob_filenames:
            batches_result = []
            for globname in batches_globnames:
                filenames = VcfLoader._glob(globname)
                if len(filenames) == 0:
                    continue
                assert len(filenames) == 1, (globname, filenames)
                batches_result.append(filenames[0])
            result.append(batches_result)
        all_filenames = list(itertools.chain.from_iterable(result))
        return all_filenames, result

    @property
    def variants_filenames(self) -> list[str]:
        return self.vcf_files

    @property
    def chromosomes(self) -> list[str]:
        """Return list of all chromosomes from VCF files."""
        result: set[str] = set()
        for filname in self.filenames:
            result.update(vcffile_chromosomes(filname))
        return [self._adjust_chrom_prefix(chrom) for chrom in result]

    def reset_regions(
        self,
        regions: list[Region] | Sequence[Region | None] | None,
    ) -> None:
        super().reset_regions(regions)
        self.vcf_loaders = None

    def _full_variants_iterator_impl(
        self,
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        if self.vcf_loaders is None:
            self.init_vcf_loaders()

        assert self.vcf_loaders is not None
        summary_index = 0
        for vcf_loader in self.vcf_loaders:
            # pylint: disable=protected-access
            iterator = vcf_loader._full_variants_iterator_impl(  # noqa: SLF001
                summary_index)
            try:
                for summary_variant, family_variants in iterator:
                    yield summary_variant, family_variants
                    summary_index += 1
            except StopIteration:
                pass

    @classmethod
    def parse_cli_arguments(
        cls, argv: argparse.Namespace, *,
        use_defaults: bool = False,
    ) -> tuple[list[str], dict[str, Any]]:
        super().parse_cli_arguments(argv, use_defaults=use_defaults)
        filenames = argv.vcf_files

        assert argv.vcf_multi_loader_fill_in_mode in {
            "reference", "unknown",
        }
        assert argv.vcf_denovo_mode in {
            "denovo", "possible_denovo", "ignore",
        }, argv.vcf_denovo_mode
        assert argv.vcf_omission_mode in {
            "omission", "possible_omission", "ignore",
        }, argv.vcf_omission_mode
        assert argv.vcf_pedigree_mode in {
            "intersection", "union", "fixed",
        }, argv.vcf_pedigree_mode

        params = {
            "vcf_include_reference_genotypes": str2bool(
                argv.vcf_include_reference_genotypes,
            ),
            "vcf_include_unknown_family_genotypes": str2bool(
                argv.vcf_include_unknown_family_genotypes,
            ),
            "vcf_include_unknown_person_genotypes": str2bool(
                argv.vcf_include_unknown_person_genotypes,
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
