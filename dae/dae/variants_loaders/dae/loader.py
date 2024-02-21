# pylint: disable=too-many-lines
# FIXME refactor and shorten this module
import os
import gzip
import warnings
import logging
import argparse
from typing import Optional, Any, Generator, Union
from contextlib import closing

import numpy as np

import pysam
import pandas as pd

import fsspec
from dae.utils.regions import Region
from dae.utils import fs_utils

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils.variant_utils import str2mat, str2mat_adjust_colsep, \
     GenotypeType, str2gt
from dae.utils.helpers import str2bool

from dae.utils.dae_utils import dae2vcf_variant

from dae.pedigrees.family import Family
from dae.pedigrees.families_data import FamiliesData
from dae.variants.attributes import Inheritance, Role
from dae.variants.core import Allele
from dae.variants.variant import SummaryVariant, SummaryVariantFactory, \
    allele_type_from_cshl_variant
from dae.variants.family_variant import FamilyVariant

from dae.variants_loaders.raw.loader import \
    VariantsGenotypesLoader, \
    TransmissionType, \
    FamiliesGenotypes, \
    CLIArgument, FamilyGenotypeIterator, FullVariantsIterator


from dae.utils.variant_utils import get_locus_ploidy


logger = logging.getLogger(__name__)


class DenovoFamiliesGenotypes(FamiliesGenotypes):
    """Tuple of family, genotype, and best_state"""
    def __init__(
            self, family: Family,
            gt: np.ndarray, best_state: Optional[np.ndarray] = None) -> None:
        super().__init__()
        self.family = family
        self.genotype = gt
        self.best_state = best_state

    def family_genotype_iterator(
        self
    ) -> Generator[tuple[Family, np.ndarray, Optional[np.ndarray]], None, None]:
        yield self.family, self.genotype, self.best_state


class DenovoLoader(VariantsGenotypesLoader):
    """Load denovo variants."""

    def __init__(
            self,
            families: FamiliesData,
            denovo_filename: str,
            genome: ReferenceGenome,
            regions: Optional[list[str]] = None,
            params: Optional[dict[str, Any]] = None,
            sort: bool = True) -> None:
        super().__init__(
            families=families,
            filenames=[denovo_filename],
            transmission_type=TransmissionType.denovo,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=False,
            params=params if params else {})

        self.genome = genome
        self.set_attribute("source_type", "denovo")
        logger.debug(
            "loading denovo variants: %s; %s", denovo_filename, self.params)

        self.denovo_df, extra_attributes = self._flexible_denovo_load_internal(
            denovo_filename,
            genome,
            families=families,
            **self.params,
        )
        self.set_attribute("extra_attributes", extra_attributes)
        self._init_chromosomes()

        if np.all(pd.isnull(self.denovo_df["genotype"])):
            self.expect_best_state = True
        elif np.all(pd.isnull(self.denovo_df["best_state"])):
            self.expect_genotype = True
        else:
            assert False
        if sort:
            self.denovo_df = self.denovo_df.sort_values(
                by=["chrom", "position", "reference", "alternative"])

    def _init_chromosomes(self) -> None:
        self._chromosomes = list(self.denovo_df.chrom.unique())
        self._chromosomes = [
            self._adjust_chrom_prefix(chrom) for chrom in self._chromosomes
        ]

        all_chromosomes = self.genome.chromosomes
        if all(chrom in set(all_chromosomes) for chrom in self._chromosomes):
            self._chromosomes = sorted(
                self._chromosomes,
                key=all_chromosomes.index)

    @property
    def chromosomes(self) -> list[str]:
        return self._chromosomes

    def reset_regions(self, regions: Optional[Union[str, list[str]]]) -> None:
        super().reset_regions(regions)

        result: list[Optional[Region]] = []
        for reg in self.regions:
            if reg is None:
                result.append(reg)
            else:
                result.append(Region.from_str(reg))
        self.regions = result  # type: ignore
        logger.debug("denovo reset regions: %s", self.regions)

    def _is_in_regions(self, summary_variant: SummaryVariant) -> bool:
        isin = [
            r.isin(  # type: ignore
                self._adjust_chrom_prefix(summary_variant.chrom),
                summary_variant.position
            )
            if r is not None
            else True
            for r in self.regions
        ]
        return any(isin)

    def _produce_family_variants(
        self, svariant: SummaryVariant,
        values: pd.Series
    ) -> list[FamilyVariant]:
        fvs = []
        extra_attributes_keys = list(filter(
            lambda x: x not in ["best_state", "family_id", "genotype"],
            values.keys()
        ))
        for f_idx, family_id in enumerate(
                values.get("family_id")):  # type: ignore
            best_state = values.get("best_state")[f_idx]  # type: ignore
            genotypes = values.get("genotype")[f_idx]  # type: ignore
            family = self.families.get(family_id)
            if family is None:
                continue
            family_genotypes = DenovoFamiliesGenotypes(
                family, genotypes, best_state)  # type: ignore
            for fam, genotype, best_state in \
                    family_genotypes.family_genotype_iterator():
                fvariant = FamilyVariant(svariant, fam, genotype, best_state)
                extra_attributes = {}
                for attr in extra_attributes_keys:
                    attr_val = values.get(attr)[f_idx]  # type: ignore
                    extra_attributes[attr] = [attr_val]
                if genotype is None:
                    fvariant.gt, fvariant._genetic_model = \
                        self._calc_genotype(  # type: ignore
                            fvariant, self.genome)
                    for fallele in fvariant.alleles:
                        fallele.gt = fvariant.gt
                        # pylint: disable=protected-access
                        fallele._genetic_model = fvariant.genetic_model
                fvariant.update_attributes(extra_attributes)
                fvs.append(fvariant)
        return fvs

    def _full_variants_iterator_impl(self) -> FullVariantsIterator:
        group = self.denovo_df.groupby(
            ["chrom", "position", "reference", "alternative"],
            sort=False).agg(list)
        for num_idx, (idx, values) in enumerate(group.iterrows()):
            chrom, position, reference, alternative = idx  # type: ignore
            position = int(position)
            summary_records = []
            for alt_index, alt in enumerate(alternative.split(",")):
                summary_records.append({
                    "chrom": chrom,
                    "reference": reference,
                    "alternative": alt,
                    "position": position,
                    "summary_variant_index": num_idx,
                    "allele_index": alt_index + 1,
                    "af_parents_called_count": None,
                    "af_parents_called_percent": None,
                    "af_allele_count": None,
                    "af_allele_freq": None,
                    "af_ref_allele_count": None,
                    "af_ref_allele_freq": None,
                })

            svariant = SummaryVariantFactory.summary_variant_from_records(
                summary_records, self.transmission_type
            )

            if not self._is_in_regions(svariant):
                continue
            fvs = self._produce_family_variants(svariant, values)
            yield svariant, fvs

    def full_variants_iterator(self) -> Generator[
        tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        full_iterator = super().full_variants_iterator()
        for summary_variants, family_variants in full_iterator:
            for fvariant in family_variants:
                for fallele in fvariant.family_alt_alleles:
                    inheritance = [
                        Inheritance.denovo
                        if vinmem is not None
                        and mem.role in set([
                            Role.prb, Role.sib, Role.unknown])
                        and inh in set([
                            Inheritance.unknown,
                            Inheritance.possible_denovo,
                            Inheritance.possible_omission])
                        else inh
                        for inh, vinmem, mem in zip(
                            fallele.inheritance_in_members,
                            fallele.variant_in_members,
                            fallele.members_in_order
                        )
                    ]
                    # pylint: disable=protected-access
                    fallele._inheritance_in_members = inheritance

            yield summary_variants, family_variants

    def close(self) -> None:
        pass

    @staticmethod
    def split_location(location: str) -> tuple[str, int]:
        chrom, position = location.split(":")
        return chrom, int(position)

    @staticmethod
    def produce_genotype(
            chrom: str,
            pos: int,
            genome: ReferenceGenome,
            family: Family,
            members_with_variant: list[str]) -> np.ndarray:
        """Produce genotype."""

        # TODO: Add support for multiallelic variants
        # This method currently assumes biallelic variants

        genotype = np.zeros(shape=(2, len(family)), dtype=GenotypeType)

        for person_id, person in family.persons.items():

            index = family.members_index([person_id])
            has_variant = int(person_id in members_with_variant)

            ploidy = get_locus_ploidy(chrom, pos, person.sex, genome)

            if ploidy == 2:
                genotype[1, index] = has_variant
            else:
                genotype[0, index] = has_variant
                genotype[1, index] = -2  # signifies haploid genotype

        return genotype

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "denovo_file",
            value_type=str,
            metavar="<variants filename>",
            help_text="DAE denovo variants file",
        ))
        arguments.append(CLIArgument(
            "--denovo-variant",
            help_text="The label or index of the"
            " column containing the CSHL-style"
            " representation of the variant."
            "[Default: variant]",
        ))
        arguments.append(CLIArgument(
            "--denovo-ref",
            help_text="The label or index of the"
            " column containing the reference"
            " allele for the variant. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-alt",
            help_text="The label or index of the "
            " column containing the alternative"
            " allele for the variant. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-location",
            # default_value="location",
            help_text="The label or index of the"
            " column containing the CSHL-style"
            " location of the variant. [Default: location]",
        ))
        arguments.append(CLIArgument(
            "--denovo-chrom",
            help_text="The label or index of the"
            " column containing the chromosome"
            " upon which the variant is located. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-pos",
            help_text="The label or index of the"
            " column containing the position"
            " upon which the variant is located. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-family-id",
            # default_value="familyId",
            help_text="The label or index of the column containing the"
            " family's ID. [Default: familyId]",
        ))
        arguments.append(CLIArgument(
            "--denovo-best-state",
            # default_value="bestState",
            help_text="The label or index of the"
            " column containing the best state"
            " for the family. [Default: bestState]",
        ))
        arguments.append(CLIArgument(
            "--denovo-genotype",
            help_text="The label or index of the"
            " column containing the family genotype."
            " [Default: genotype]",
        ))
        arguments.append(CLIArgument(
            "--denovo-person-id",
            help_text="The label or index of the column containing the"
            " person's ID. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-sep",
            value_type=str,
            default_value="\t",
            help_text="Denovo file field separator [default: `\\t`]",
        ))
        return arguments

    # flake8: noqa: C901
    @classmethod
    def parse_cli_arguments(
        cls, argv: argparse.Namespace,
        use_defaults: bool = False
    ) -> tuple[list[str], dict[str, Any]]:
        # pylint: disable=too-many-branches
        logger.debug("CLI arguments: %s", argv)

        if argv.denovo_location and (argv.denovo_chrom or argv.denovo_pos):
            logger.error(
                "--denovo-location and (--denovo-chrom, --denovo-pos) "
                "are mutually exclusive"
            )
            raise ValueError()

        if argv.denovo_variant and (argv.denovo_ref or argv.denovo_alt):
            logger.error(
                "--denovo-variant and (denovo-ref, denovo-alt) "
                "are mutually exclusive"
            )
            raise ValueError()

        if argv.denovo_person_id and (
                argv.denovo_family_id or argv.denovo_best_state):
            logger.error(
                "--denovo-person-id and (denovo-family-id, denovo-best-state) "
                "are mutually exclusive"
            )
            raise ValueError()

        if not (argv.denovo_location
                or (argv.denovo_chrom and argv.denovo_pos)):
            argv.denovo_location = "location"

        if not (argv.denovo_variant or (argv.denovo_ref and argv.denovo_alt)):
            argv.denovo_variant = "variant"

        if not (argv.denovo_person_id
                or (argv.denovo_family_id and (
                    argv.denovo_best_state or argv.denovo_genotype))):
            argv.denovo_family_id = "familyId"
            argv.denovo_best_state = "bestState"

        if not argv.denovo_location:
            if not argv.denovo_chrom:
                argv.denovo_chrom = "CHROM"
            if not argv.denovo_pos:
                argv.denovo_pos = "POS"

        if not argv.denovo_variant:
            if not argv.denovo_ref:
                argv.denovo_ref = "REF"
            if not argv.denovo_alt:
                argv.denovo_alt = "ALT"

        if not argv.denovo_person_id:
            if not argv.denovo_family_id:
                argv.denovo_family_id = "familyId"
            if not argv.denovo_best_state and not argv.denovo_genotype:
                argv.denovo_best_state = "bestState"
        assert not (argv.denovo_best_state and argv.denovo_genotype)

        if argv.denovo_sep is None:
            argv.denovo_sep = "\t"

        params = {
            "denovo_location": argv.denovo_location,
            "denovo_variant": argv.denovo_variant,
            "denovo_chrom": argv.denovo_chrom,
            "denovo_pos": argv.denovo_pos,
            "denovo_ref": argv.denovo_ref,
            "denovo_alt": argv.denovo_alt,
            "denovo_person_id": argv.denovo_person_id,
            "denovo_family_id": argv.denovo_family_id,
            "denovo_best_state": argv.denovo_best_state,
            "denovo_genotype": argv.denovo_genotype,
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
            "denovo_sep": argv.denovo_sep,
        }

        return argv.denovo_file, params

    def _flexible_denovo_load_internal(
            self,
            filepath: str,
            genome: ReferenceGenome,
            families: FamiliesData,
            denovo_location: Optional[str] = None,
            denovo_variant: Optional[str] = None,
            denovo_chrom: Optional[str] = None,
            denovo_pos: Optional[str] = None,
            denovo_ref: Optional[str] = None,
            denovo_alt: Optional[str] = None,
            denovo_person_id: Optional[str] = None,
            denovo_family_id: Optional[str] = None,
            denovo_best_state: Optional[str] = None,
            denovo_genotype: Optional[str] = None,
            denovo_sep: str = "\t",
            **_kwargs: Any) -> tuple[pd.DataFrame, Any]:
        # FIXME
        # pylint: disable=too-many-arguments,too-many-branches
        # pylint: disable=too-many-statements,too-many-locals
        assert families is not None
        assert isinstance(
            families, FamiliesData
        ), "families must be an instance of FamiliesData!"
        assert genome, "You must provide a genome object!"

        if not (denovo_location or (denovo_chrom and denovo_pos)):
            denovo_location = "location"

        if not (denovo_variant or (denovo_ref and denovo_alt)):
            denovo_variant = "variant"

        if not (denovo_person_id
                or (denovo_family_id
                    and (denovo_best_state or denovo_genotype))):
            denovo_family_id = "familyId"
            denovo_best_state = "bestState"

        if denovo_sep is None:
            denovo_sep = "\t"

        with warnings.catch_warnings(record=True) as _:
            warnings.filterwarnings(
                "ignore",
                category=pd.errors.ParserWarning,
                message="Both a converter and dtype were specified",
            )

            raw_df = pd.read_csv(
                filepath,
                sep=denovo_sep,
                converters={
                    denovo_pos: lambda p: int(p) if p else None,  # type: ignore
                } if denovo_pos is not None else {},
                dtype=str,
                comment="#",
                encoding="utf-8",
                na_filter=False)

        if denovo_location:
            chrom_col, pos_col = zip(
                *map(self.split_location, raw_df[denovo_location])
            )
        else:
            assert denovo_chrom is not None
            assert denovo_pos is not None
            chrom_col = raw_df.loc[:, denovo_chrom]  # type: ignore
            pos_col = raw_df.loc[:, denovo_pos]  # type: ignore

        if denovo_variant:
            variant_col = raw_df.loc[:, denovo_variant]
            ref_alt_tuples = [
                dae2vcf_variant(
                    self._adjust_chrom_prefix(variant_tuple[0]),
                    variant_tuple[1], variant_tuple[2],
                    genome
                ) for variant_tuple in zip(chrom_col, pos_col, variant_col)
            ]
            pos_col, ref_col, alt_col = zip(*ref_alt_tuples)

        else:
            assert denovo_ref is not None
            assert denovo_alt is not None
            ref_col = raw_df.loc[:, denovo_ref]
            alt_col = raw_df.loc[:, denovo_alt]

        extra_attributes_cols = raw_df.columns.difference([
            denovo_location, denovo_variant, denovo_chrom, denovo_pos,
            denovo_ref, denovo_alt, denovo_person_id, denovo_family_id,
            denovo_best_state, denovo_genotype
        ])

        if denovo_person_id:
            if denovo_family_id in raw_df.columns:
                temp_df = pd.DataFrame(
                    {
                        "chrom": chrom_col,
                        "pos": pos_col,
                        "ref": ref_col,
                        "alt": alt_col,
                        "family_id": raw_df.loc[:, denovo_family_id],
                        "person_id": raw_df.loc[:, denovo_person_id],
                    }
                )
                grouped = temp_df.groupby(
                    ["chrom", "pos", "ref", "alt", "family_id"])
            else:
                temp_df = pd.DataFrame(
                    {
                        "chrom": chrom_col,
                        "pos": pos_col,
                        "ref": ref_col,
                        "alt": alt_col,
                        "person_id": raw_df.loc[:, denovo_person_id],
                    }
                )

                grouped = temp_df.groupby(["chrom", "pos", "ref", "alt"])

            result = []

            # TODO Implement support for multiallelic variants
            for variant, variants_indices in grouped.groups.items():
                # Here we join and then split again by ',' to handle cases
                # where the person IDs are actually a list of IDs, separated
                # by a ','
                person_ids = ",".join(
                    temp_df.iloc[
                        variants_indices].loc[:, "person_id"]  # type: ignore
                ).replace(";", ",").split(",")
                if "family_id" in temp_df.columns:
                    family_id = variant[4]  # type: ignore
                    variant_families = {
                        families.persons[(family_id, pid)].family_id
                        for pid in person_ids}
                else:
                    variant_families = set()
                    for person_id in person_ids:
                        if len(families.persons_by_person_id[person_id]) == 0:
                            continue
                        if len(families.persons_by_person_id[person_id]) == 1:
                            variant_families.add(
                                families.persons_by_person_id[person_id][0].family_id
                            )
                        else:
                            logger.warning(
                                "person %s is in multiple families: %s",
                                person_id,
                                [
                                    f.family_id
                                    for f in families.persons_by_person_id[
                                        person_id
                                    ]
                                ],
                            )
                            raise ValueError(
                                f"person {person_id} in multiple families")

                # TODO Implement support for multiallelic variants
                for family_id in variant_families:
                    family = families[family_id]
                    family_dict = {
                        "chrom": variant[0],  # type: ignore
                        "position": variant[1],  # type: ignore
                        "reference": variant[2],  # type: ignore
                        "alternative": variant[3],  # type: ignore
                        "family_id": family_id,
                        "genotype": self.produce_genotype(
                            variant[0],  # type: ignore
                            variant[1],  # type: ignore
                            genome,
                            family,
                            person_ids,
                        ),
                        "best_state": None,
                    }
                    record = raw_df.loc[variants_indices[0]]  # type: ignore
                    extra_attributes = record[extra_attributes_cols].to_dict()

                    result.append({**family_dict, **extra_attributes})

            denovo_df = pd.DataFrame(result)

        else:
            family_col = raw_df.loc[:, denovo_family_id]
            if denovo_best_state:
                best_state_col = list(
                    map(
                        str2mat_adjust_colsep,
                        raw_df[denovo_best_state],
                    )
                )
                # genotype_col = list(map(best2gt, best_state_col))

                denovo_df = pd.DataFrame(
                    {
                        "chrom": chrom_col,
                        "position": pos_col,
                        "reference": ref_col,
                        "alternative": alt_col,
                        "family_id": family_col,
                        "genotype": None,
                        "best_state": best_state_col,
                    }
                )
            else:
                assert denovo_genotype
                genotype_col = list(
                    map(
                        str2gt,
                        raw_df[denovo_genotype],
                    )
                )
                # genotype_col = list(map(best2gt, best_state_col))

                denovo_df = pd.DataFrame(
                    {
                        "chrom": chrom_col,
                        "position": pos_col,
                        "reference": ref_col,
                        "alternative": alt_col,
                        "family_id": family_col,
                        "genotype": genotype_col,
                        "best_state": None,
                    }
                )

            extra_attributes_df = raw_df[extra_attributes_cols]
            denovo_df = denovo_df.join(extra_attributes_df)

        return (denovo_df, extra_attributes_cols.tolist())

    def flexible_denovo_load(
            self,
            filepath: str,
            genome: ReferenceGenome,
            families: FamiliesData,
            denovo_location: Optional[str] = None,
            denovo_variant: Optional[str] = None,
            denovo_chrom: Optional[str] = None,
            denovo_pos: Optional[str] = None,
            denovo_ref: Optional[str] = None,
            denovo_alt: Optional[str] = None,
            denovo_person_id: Optional[str] = None,
            denovo_family_id: Optional[str] = None,
            denovo_best_state: Optional[str] = None,
            denovo_genotype: Optional[str] = None,
            denovo_sep: str = "\t",
            **kwargs: Any) -> pd.DataFrame:
        """Load de Novo variants from a file.

        Read a text file containing variants in the form
        of delimiter-separted values and produce a dataframe.

        The text file may use different names for the columns
        containing the relevant data - these are specified
        with the provided parameters.

        :param str filepath: The path to the DSV file to read.

        :param genome: A reference genome object.

        :param str denovo_location: The label or index of the column containing
        the CSHL-style location of the variant.

        :param str denovo_variant: The label or index of the column containing
        the CSHL-style representation of the variant.

        :param str denovo_chrom: The label or index of the column containing
        the chromosome upon which the variant is located.

        :param str denovo_pos: The label or index of the column containing the
        position upon which the variant is located.

        :param str denovo_ref: The label or index of the column containing the
        variant's reference allele.

        :param str denovo_alt: The label or index of the column containing the
        variant's alternative allele.

        :param str denovo_person_id: The label or index of the column
        containing either a singular person ID or a comma-separated
        list of person IDs.

        :param str denovo_family_id: The label or index of the column
        containing a singular family ID.

        :param str denovo_best_state: The label or index of the column
        containing the best state for the variant.

        :param str families: An instance of the FamiliesData class for the
        pedigree of the relevant study.

        :type genome: An instance of Genome.

        :return: Dataframe containing the variants, with the following
        header - 'chrom', 'position', 'reference', 'alternative', 'family_id',
        'genotype'.

        :rtype: An instance of Pandas' DataFrame class.
        """
        # FIXME too many arguments
        # pylint: disable=too-many-arguments
        denovo_df, _ = self._flexible_denovo_load_internal(
            filepath,
            genome,
            families,
            denovo_location=denovo_location,
            denovo_variant=denovo_variant,
            denovo_chrom=denovo_chrom,
            denovo_pos=denovo_pos,
            denovo_ref=denovo_ref,
            denovo_alt=denovo_alt,
            denovo_person_id=denovo_person_id,
            denovo_family_id=denovo_family_id,
            denovo_best_state=denovo_best_state,
            denovo_genotype=denovo_genotype,
            denovo_sep=denovo_sep,
            **kwargs
        )
        return denovo_df


class DaeTransmittedFamiliesGenotypes(FamiliesGenotypes):
    """Tuple of families and family data"""
    def __init__(
        self, families: FamiliesData,
        family_data: dict[str, tuple[np.ndarray, np.ndarray]]
    ) -> None:
        super().__init__()
        self.families = families
        self.family_data = family_data

    def get_family_read_counts(self, family: Family) -> Optional[np.ndarray]:
        fdata = self.family_data.get(family.family_id, None)
        if fdata is None:
            return None
        return fdata[1]

    def family_genotype_iterator(
        self
    ) -> FamilyGenotypeIterator:
        for family_id, (best_state, read_counts) in self.family_data.items():
            fam = self.families.get(family_id)
            if fam is None:
                continue
            assert best_state is not None, (family_id, best_state, read_counts)

            yield fam, best_state, read_counts


class DaeTransmittedLoader(VariantsGenotypesLoader):
    """Loader for dae variants."""

    def __init__(
        self,
        families: FamiliesData,
        summary_filename: str,
        genome: ReferenceGenome,
        regions: None=None,
        params: Optional[dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> None:
        toomany_filename = DaeTransmittedLoader._build_toomany_filename(
            summary_filename
        )
        params = params if params else {}

        super().__init__(
            families=families,
            filenames=[summary_filename, toomany_filename],
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=True,
            params=params,
        )

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename

        self.set_attribute("source_type", "dae")

        self.genome = genome

        self.params = params
        self.include_reference = self.params.get(
            "dae_include_reference_genotypes", False
        )
        try:
            # pylint: disable=no-member
            with pysam.Tabixfile(self.summary_filename) as tbx:
                self._chromosomes = \
                    [self._adjust_chrom_prefix(chrom) for chrom in tbx.contigs]
        except Exception:  # pylint: disable=broad-except
            self._chromosomes = self.genome.chromosomes

    @property
    def chromosomes(self) -> list[str]:
        return self._chromosomes

    @property
    def variants_filenames(self) -> list[str]:
        return [self.summary_filename]

    @staticmethod
    def _build_toomany_filename(summary_filename: str) -> str:
        assert fs_utils.exists(
            f"{summary_filename}.tbi"
        ), f"summary filename tabix index missing {summary_filename}"

        dirname = os.path.dirname(summary_filename)
        basename = os.path.basename(summary_filename)
        if basename.endswith(".txt.bgz"):
            result = os.path.join(dirname, f"{basename[:-8]}-TOOMANY.txt.bgz")
        elif basename.endswith(".txt.gz"):
            result = os.path.join(dirname, f"{basename[:-7]}-TOOMANY.txt.gz")
        else:
            assert False, (
                f"Bad summary filename {summary_filename}: "
                f"unexpected extention"
            )

        assert fs_utils.exists(result), f"missing TOOMANY file {result}"
        assert fs_utils.exists(
            f"{result}.tbi"
        ), f"missing tabix index for TOOMANY file {result}"

        return result

    @staticmethod
    def _rename_columns(columns: list[str]) -> list[str]:
        if "#chr" in columns:
            columns[columns.index("#chr")] = "chrom"
        if "chr" in columns:
            columns[columns.index("chr")] = "chrom"
        if "position" in columns:
            columns[columns.index("position")] = "cshl_position"
        if "variant" in columns:
            columns[columns.index("variant")] = "cshl_variant"
        return columns

    @staticmethod
    def _load_column_names(filename: str) -> list[str]:
        with fsspec.open(filename) as rawfile:
            with gzip.open(rawfile) as infile:
                column_names = (
                    infile.readline().decode("utf-8").strip().split("\t")
                )
        return column_names

    @classmethod
    def _load_toomany_columns(cls, toomany_filename: str) -> list[str]:
        toomany_columns = cls._load_column_names(toomany_filename)
        return cls._rename_columns(toomany_columns)

    @classmethod
    def _load_summary_columns(cls, summary_filename: str) -> list[str]:
        summary_columns = cls._load_column_names(summary_filename)
        return cls._rename_columns(summary_columns)

    def _summary_variant_from_dae_record(
        self, summary_index: int, rec: dict[str, Any]
    ) -> SummaryVariant:
        rec["cshl_position"] = int(rec["cshl_position"])
        chrom = rec["chrom"]
        # chrom = self._adjust_chrom_prefix(rec["chrom"])
        position, reference, alternative = dae2vcf_variant(
            chrom,
            rec["cshl_position"],
            rec["cshl_variant"],
            self.genome,
        )
        allele = Allele.build_vcf_allele(
            chrom, position, reference, alternative)
        rec["chrom"] = allele.chrom
        rec["position"] = allele.position
        rec["end_position"] = allele.end_position
        rec["reference"] = allele.reference
        rec["alternative"] = allele.alternative
        rec["all.nParCalled"] = int(rec["all.nParCalled"])
        rec["all.nAltAlls"] = int(rec["all.nAltAlls"])
        rec["all.prcntParCalled"] = float(rec["all.prcntParCalled"])
        rec["all.altFreq"] = float(rec["all.altFreq"])
        rec["summary_variant_index"] = summary_index

        parents_called = int(rec.get("all.nParCalled", 0))
        ref_allele_count = 2 * int(rec.get("all.nParCalled", 0)) - int(
            rec.get("all.nAltAlls", 0)
        )
        ref_allele_prcnt = 0.0
        if parents_called > 0:
            ref_allele_prcnt = ref_allele_count / 2.0 / parents_called
        ref = {
            "chrom": rec["chrom"],
            "position": rec["position"],
            "end_position": rec["position"],
            "reference": rec["reference"],
            "alternative": None,
            "variant_type": None,
            "cshl_position": rec["cshl_position"],
            "cshl_variant": rec["cshl_variant"],
            "summary_variant_index": rec["summary_variant_index"],
            "allele_index": 0,
            "af_parents_called_count": parents_called,
            "af_parents_called_percent": float(
                rec.get("all.prcntParCalled", 0.0)
            ),
            "af_allele_count": ref_allele_count,
            "af_allele_freq": ref_allele_prcnt,
            "hw": rec.get("HW"),
        }

        alt = {
            "chrom": rec["chrom"],
            "position": rec["position"],
            "end_position": rec["end_position"],
            "reference": rec["reference"],
            "alternative": rec["alternative"],
            "variant_type": allele_type_from_cshl_variant(rec["cshl_variant"]),
            "cshl_position": rec["cshl_position"],
            "cshl_variant": rec["cshl_variant"],
            "summary_variant_index": rec["summary_variant_index"],
            "allele_index": 1,
            "af_parents_called_count": int(rec.get("all.nParCalled", 0)),
            "af_parents_called_percent": float(
                rec.get("all.prcntParCalled", 0.0)
            ),
            "af_allele_count": int(rec.get("all.nAltAlls", 0)),
            "af_allele_freq": float(rec.get("all.altFreq", 0.0)),
            "hw": rec.get("HW"),
        }
        summary_variant = SummaryVariantFactory.summary_variant_from_records(
            [ref, alt], transmission_type=self.transmission_type
        )
        return summary_variant

    @staticmethod
    def _explode_family_data(
        family_data: str
    ) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        best_states = {
            fid: (
                str2mat(bs, col_sep="", row_sep="/"),
                str2mat(rc, col_sep=" ", row_sep="/", dtype=np.int16)
            )
            for (fid, bs, rc) in [
                fg.split(":") for fg in family_data.split(";")
            ]
        }
        return best_states

    # @staticmethod
    # def _explode_family_read_counts(family_data):
    #     read_counts = {
    #         fid: str2mat(rc, col_sep=" ", row_sep="/")
    #         for (fid, _bs, rc) in [
    #             fg.split(":") for fg in family_data.split(";")
    #         ]
    #     }
    #     return read_counts

    def close(self) -> None:
        pass

    def _produce_family_variants(
        self, summary_variant: SummaryVariant,
        families_genotypes: DaeTransmittedFamiliesGenotypes
    ) -> list[FamilyVariant]:
        family_variants = []
        for (fam, best_state, read_counts) in \
                families_genotypes.family_genotype_iterator():

            fvariant = FamilyVariant(
                summary_variant, fam, None, best_state)
            fvariant.gt, fvariant._genetic_model = \
                self._calc_genotype(
                    fvariant, self.genome)
            for fallele in fvariant.alleles:
                fallele.gt = fvariant.gt  # type: ignore
                # pylint: disable=protected-access
                fallele._genetic_model = fvariant._genetic_model  # type: ignore
                fallele.update_attributes({"read_counts": read_counts})
            family_variants.append(fvariant)
        return family_variants

    def _full_variants_iterator_impl(self) -> FullVariantsIterator:

        summary_columns = self._load_summary_columns(self.summary_filename)
        toomany_columns = self._load_toomany_columns(self.toomany_filename)

        summary_index = 0
        for region in self.regions:
            try:
                # using a context manager because of
                # https://stackoverflow.com/a/25968716/2316754
                # pylint: disable=no-member
                with closing(pysam.Tabixfile(self.summary_filename)) \
                        as sum_tbf, \
                        closing(pysam.Tabixfile(self.toomany_filename)) \
                        as too_tbf:

                    region_unadjusted = (
                        self._unadjust_chrom_prefix(region)
                        if region is not None
                        else None
                    )
                    summary_iterator = sum_tbf.fetch(
                        region=region_unadjusted, parser=pysam.asTuple()
                    )
                    toomany_iterator = too_tbf.fetch(
                        region=region_unadjusted, parser=pysam.asTuple()
                    )

                    for summary_line in summary_iterator:
                        rec = dict(zip(summary_columns, summary_line))
                        try:
                            summary_variant = \
                                self._summary_variant_from_dae_record(
                                    summary_index, rec)

                            family_data = rec["familyData"]
                            if family_data == "TOOMANY":
                                toomany_line = next(toomany_iterator, None)
                                if toomany_line is None:
                                    return
                                toomany_rec = dict(zip(
                                    toomany_columns, toomany_line))
                                family_data = toomany_rec["familyData"]

                                assert rec["cshl_position"] == int(
                                    toomany_rec["cshl_position"]
                                )

                            family_data = self._explode_family_data(
                                family_data)

                            families_genotypes = \
                                DaeTransmittedFamiliesGenotypes(
                                    self.families, family_data)
                            family_variants = self._produce_family_variants(
                                summary_variant, families_genotypes)

                            yield summary_variant, family_variants
                            summary_index += 1
                        except Exception:  # pylint: disable=broad-except
                            logger.error(
                                "unable to process summary line: %s "
                                "from %s: %s",
                                summary_line, self.summary_filename,
                                self.regions,
                                exc_info=True)

            except ValueError:
                logger.warning(
                    "could not find region %s in %s or %s",
                    region, self.summary_filename, self.toomany_filename,
                    exc_info=True)

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "dae_summary_file",
            value_type=str,
            metavar="<summary filename>",
            help_text="summary variants file to import",
        ))
        arguments.append(CLIArgument(
            "--dae-include-reference-genotypes",
            default_value=False,
            help_text="fill in reference only variants [default: %(default)s]",
            action="store_true",
        ))
        return arguments

    @classmethod
    def parse_cli_arguments(
        cls, argv: argparse.Namespace, use_defaults: bool = False
    ) -> tuple[list[str], dict[str, Any]]:
        filename = argv.dae_summary_file

        params = {
            "dae_include_reference_genotypes": str2bool(
                argv.dae_include_reference_genotypes
            ),
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
        }
        return filename, params
