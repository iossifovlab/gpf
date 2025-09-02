"""Defines CNV loader class and helpers.

Copy Number Variants (CNV) loader :class:`CNVLoader`
====================================================

This modules provides a class :class:`CNVLoader` to facilitate loading CNVs
specified in various input formats.

There are three groups of input parameters that could be configured
by the CNVLoader parameters:

- location of the variant - VCF-like vs CSHL-like of the variant position;

- variant genotype - list of person_ids vs CSHL-like family/best state
  description of the genotype for given family

- variant type - flexible CNV+/CNV- variant type description.

To configure the :class:`CNVLoader` you need to pass `params` dictionary
to the constructor of the class.

Parameters that are used to configure input data colums are:

Location of the CNVs
--------------------

- `cnv_location` - column name, that is interpreted as variant
  location

- `cnv_chrom` - column name, interpreted as the chromosome

- `cnv_start` - column name, interpreted as the start position of the CNVs

- `cnv_end` - column name, interpreted as the end position of the CNVs


Genotype of the CNVs
--------------------

- `cnv_family_id` - column name, specifying the family for the CNVs

- `cnv_best_state` - column name, specifying the best state fore the CNVs

- `cnv_person_id` - column name, specifying a person, that has given CNV


Variant type for CNVs
---------------------


- `cnv_variant_type` - column name, specifying the CNV variant type

- `cnv_plus_values` - list of the values in column `cnv_variant_type` that
  are interpreted as `CNV+`

- `cnv_minus_values` - list of values in column `cnv_variant_type` that are
  interpreted as `CNV-`

Additional parameters
---------------------

Additional parameters, that configure the behavior of the :class:`CNVLoader`
are:

- `cnv_sep` - separator character, that split columns in the lines of the
  input file

- `cnv_transmission_type` - the CNV loader is used mostly for importing
  de Novo variants. In rare cases when we use this loader to import
  transmitted CNV variants we should pass this parameter to specify
  that the varirants are not `denovo`.


"""
import argparse
import logging
from collections.abc import Generator
from copy import copy
from pathlib import Path
from typing import Any, TextIO

import pandas as pd

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants_loaders.cnv.flexible_cnv_loader import flexible_cnv_loader
from dae.variants_loaders.raw.loader import (
    CLIArgument,
    FullVariantsIterator,
    TransmissionType,
    VariantsGenotypesLoader,
)

logger = logging.getLogger(__name__)


def _cnv_loader(
    filepath_or_buffer: str | Path | TextIO,
    families: FamiliesData,
    genome: ReferenceGenome, *,
    cnv_chrom: str | None = None,
    cnv_start: str | None = None,
    cnv_end: str | None = None,
    cnv_location: str | None = None,
    cnv_person_id: str | None = None,
    cnv_family_id: str | None = None,
    cnv_best_state: str | None = None,
    cnv_variant_type: str | None = None,
    cnv_plus_values: list[str] | None = None,
    cnv_minus_values: list[str] | None = None,
    cnv_sep: str = "\t",
    **kwargs: Any,
) -> pd.DataFrame:
    """Flexible load of CNV variants.

    This function uses flexible variant loader infrastructure to
    load variants from a CNVs data input and transform them into a pandas
    `DataFrame`.
    """
    # pylint: disable=too-many-arguments,too-many-locals
    logger.info("unexpected parameters passed to _cnv_loader: %s", kwargs)

    variant_generator = flexible_cnv_loader(
        filepath_or_buffer,
        families,
        genome,
        cnv_chrom=cnv_chrom,
        cnv_start=cnv_start,
        cnv_end=cnv_end,
        cnv_location=cnv_location,
        cnv_person_id=cnv_person_id,
        cnv_family_id=cnv_family_id,
        cnv_best_state=cnv_best_state,
        cnv_variant_type=cnv_variant_type,
        cnv_plus_values=cnv_plus_values,
        cnv_minus_values=cnv_minus_values,
        cnv_sep=cnv_sep,
    )

    data = list(variant_generator)

    df: pd.DataFrame = pd.DataFrame.from_records(
        data, columns=[
            "chrom", "pos", "pos_end",
            "variant_type",
            "family_id", "best_state",
        ])

    df = df.sort_values(
        by=["chrom", "pos", "pos_end"])

    return df.rename(
        columns={
            "pos": "position",
            "pos_end": "end_position",
        })


class CNVLoader(VariantsGenotypesLoader):
    """Defines CNV loader class."""

    def __init__(
            self,
            families: FamiliesData,
            cnv_filenames: list[str | Path | TextIO],
            genome: ReferenceGenome,
            regions: list[Region] | None = None,
            params: dict[str, Any] | None = None):

        if params is None:
            params = {}
        if params.get("cnv_transmission_type") == "denovo":
            transmission_type = TransmissionType.denovo
        else:
            transmission_type = TransmissionType.transmitted

        super().__init__(
            families=families,
            filenames=[str(fn) for fn in cnv_filenames],
            transmission_type=transmission_type,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=True,
            params=params,
        )

        logger.info("CNV loader params: %s", params)
        self.genome = genome
        self.set_attribute("source_type", "cnv")

        assert isinstance(cnv_filenames, list)
        assert len(cnv_filenames) == 1
        cnv_filename = cnv_filenames[0]

        logger.info("CNV loader params: %s", self.params)
        self.cnv_df = _cnv_loader(
            cnv_filename,
            families,
            genome,
            **self.params,
        )

        self._init_chromosomes()

    def _init_chromosomes(self) -> None:
        self._chromosomes = list(self.cnv_df.chrom.unique())
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

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "cnv_file",
            value_type=str,
            metavar="<variants filename>",
            help_text="cnv variants file",
        ))
        arguments.append(CLIArgument(
            "--cnv-location",
            value_type=str,
            default_value="location",
            help_text="The label or index of the"
            " column containing the CSHL-style"
            " location of the variant. [Default: location]",
        ))
        arguments.append(CLIArgument(
            "--cnv-family-id",
            value_type=str,
            default_value="familyId",
            help_text="The label or index of the"
            " column containing family's ID."
            " [Default: familyId]",
        ))
        arguments.append(CLIArgument(
            "--cnv-best-state",
            value_type=str,
            default_value="bestState",
            help_text="The label or index of the"
            " column containing the variant's"
            " best state. [Default: bestState]",
        ))
        arguments.append(CLIArgument(
            "--cnv-person-id",
            value_type=str,
            help_text="The label or index of the"
            " column containing the ids of the people in which"
            " the variant is. [Default: None]",
        ))
        arguments.append(CLIArgument(
            "--cnv-variant-type",
            value_type=str,
            default_value="variant",
            help_text="The label or index of the"
            " column containing the variant's"
            " type. [Default: variant]",
        ))
        arguments.append(CLIArgument(
            "--cnv-plus-values",
            value_type=str,
            default_value="CNV+",
            help_text="The cnv+ value used in the columns containing"
            " the variant's type. [Default: CNV+]",
        ))
        arguments.append(CLIArgument(
            "--cnv-minus-values",
            value_type=str,
            default_value="CNV-",
            help_text="The cnv- value used in the columns containing"
            " the variant's type. [Default: CNV-]",
        ))
        arguments.append(CLIArgument(
            "--cnv-sep",
            value_type=str,
            default_value="\t",
            help_text="CNV file field separator. [Default: `\\t`]",
        ))
        arguments.append(CLIArgument(
            "--cnv-transmission-type",
            value_type=str,
            default_value="denovo",
            help_text="CNV transmission type. [Default: `denovo`]",
        ))
        return arguments

    def _is_in_regions(self, summary_variant: SummaryVariant) -> bool:
        if self.regions == [None]:
            return True
        isin = [
            True if r is None else r.isin(
                self._adjust_chrom_prefix(summary_variant.chrom),
                summary_variant.position,
            )
            for r in self.regions
        ]
        return any(isin)

    def close(self) -> None:
        pass

    def _full_variants_iterator_impl(
        self,
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        # pylint: disable=too-many-locals
        group = self.cnv_df.groupby(
            ["chrom", "position", "end_position", "variant_type"],
            sort=False).agg(list)

        for num_idx, (idx, values) in enumerate(group.iterrows()):

            chrom, position, end_position, variant_type = idx  # type: ignore
            position: int = int(position)  # type: ignore
            end_position: int = int(end_position)  # type: ignore
            summary_rec: dict[str, Any] = {
                "chrom": chrom,  # type: ignore
                "reference": None,
                "alternative": None,
                "position": position,  # type: ignore
                "end_position": end_position,  # type: ignore
                "summary_index": num_idx,
                "variant_type": variant_type,  # type: ignore
                "allele_index": 0,
                "af_parents_called_count": None,
                "af_parents_called_percent": None,
                "af_allele_count": None,
                "af_allele_freq": None,
                "af_ref_allele_count": None,
                "af_ref_allele_freq": None,
            }
            alt_rec = copy(summary_rec)
            del summary_rec["end_position"]
            del summary_rec["variant_type"]

            alt_rec["allele_index"] = 1

            svar = SummaryVariantFactory.summary_variant_from_records(
                [summary_rec, alt_rec], self.transmission_type,
            )

            if not self._is_in_regions(svar):
                continue

            fvs = []
            extra_attributes_keys = filter(
                lambda x: x not in ["best_state", "family_id"],
                values.keys(),
            )
            for f_idx, family_id in enumerate(
                    values.get("family_id")):  # type: ignore
                best_state = values.get("best_state")[f_idx]  # type: ignore
                assert best_state is not None

                family = self.families.get(family_id)
                if family is None:
                    continue
                fvar = FamilyVariant(
                    svar, family, None, best_state)  # type: ignore
                extra_attributes = {}
                for attr in extra_attributes_keys:
                    attr_val = values.get(attr)[f_idx]  # type: ignore
                    extra_attributes[attr] = [attr_val]
                fvar.update_attributes(extra_attributes)
                fvs.append(fvar)
            yield svar, fvs

    def full_variants_iterator(self) -> FullVariantsIterator:
        full_iterator = super().full_variants_iterator()

        for summary_variants, family_variants in full_iterator:
            for fvar in family_variants:
                for fa in fvar.family_alt_alleles:
                    if self.transmission_type != TransmissionType.denovo:
                        continue
                    inheritance = [
                        Inheritance.denovo if mem is not None else inh
                        for inh, mem in zip(
                            fa.inheritance_in_members,
                            fa.variant_in_members,
                            strict=True,
                        )
                    ]
                    # pylint: disable=protected-access
                    fa._inheritance_in_members = inheritance  # noqa: SLF001

            yield summary_variants, family_variants

    @classmethod
    def parse_cli_arguments(
        cls, argv: argparse.Namespace, *,
        use_defaults: bool = False,  # noqa: ARG003
    ) -> tuple[list[str], dict[str, Any]]:
        if argv.cnv_file is None:
            return [], {}
        return [argv.cnv_file], {
            "cnv_location": argv.cnv_location,
            "cnv_person_id": argv.cnv_person_id,
            "cnv_family_id": argv.cnv_family_id,
            "cnv_variant_type": argv.cnv_variant_type,
            "cnv_plus_values": argv.cnv_plus_values,
            "cnv_minus_values": argv.cnv_minus_values,
            "cnv_best_state": argv.cnv_best_state,
            "cnv_sep": argv.cnv_sep,
            "cnv_transmission_type": argv.cnv_transmission_type,
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
        }
