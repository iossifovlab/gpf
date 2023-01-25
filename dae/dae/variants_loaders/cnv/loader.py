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
import logging
import argparse
from pathlib import Path
from copy import copy

from typing import List, Optional, Dict, Any, Tuple, Generator, \
    Union, TextIO

import pandas as pd

from dae.variants_loaders.cnv.flexible_cnv_loader import flexible_cnv_loader
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.variants_loaders.raw.loader import VariantsGenotypesLoader, \
    TransmissionType

from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Inheritance
from dae.variants.variant import SummaryVariantFactory, SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.variants_loaders.raw.loader import CLIArgument

from dae.utils.regions import Region


logger = logging.getLogger(__name__)


def _cnv_loader(
        filepath_or_buffer: Union[str, Path, TextIO],
        families: FamiliesData,
        genome: ReferenceGenome,
        cnv_chrom: Optional[str] = None,
        cnv_start: Optional[str] = None,
        cnv_end: Optional[str] = None,
        cnv_location: Optional[str] = None,
        cnv_person_id: Optional[str] = None,
        cnv_family_id: Optional[str] = None,
        cnv_best_state: Optional[str] = None,
        cnv_variant_type: Optional[str] = None,
        cnv_plus_values: Optional[List[str]] = None,
        cnv_minus_values: Optional[List[str]] = None,
        cnv_sep: str = "\t",
        **kwargs) -> pd.DataFrame:
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

    data = []
    for record in variant_generator:
        data.append(record)

    df: pd.DataFrame = pd.DataFrame.from_records(  # type: ignore
        data, columns=[
            "chrom", "pos", "pos_end",
            "variant_type",
            "family_id", "best_state"
        ])

    df = df.sort_values(
        by=["chrom", "pos", "pos_end"])

    df = df.rename(
        columns={
            "pos": "position",
            "pos_end": "end_position"
        })
    return df


class CNVLoader(VariantsGenotypesLoader):
    """Defines CNV loader class."""

    def __init__(
            self,
            families: FamiliesData,
            cnv_filenames: List[str],
            genome: ReferenceGenome,
            regions: Optional[List[str]] = None,
            params: Optional[Dict[str, Any]] = None):

        if params is None:
            params = {}
        if params.get("cnv_transmission_type") == "denovo":
            transmission_type = TransmissionType.denovo
        else:
            transmission_type = TransmissionType.transmitted

        super().__init__(
            families=families,
            filenames=cnv_filenames,
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
        self.reset_regions(regions)

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

    def _init_chromosomes(self):
        self.chromosomes = list(self.cnv_df.chrom.unique())
        self.chromosomes = [
            self._adjust_chrom_prefix(chrom) for chrom in self.chromosomes
        ]

        all_chromosomes = self.genome.chromosomes
        if all(chrom in set(all_chromosomes) for chrom in self.chromosomes):
            self.chromosomes = sorted(
                self.chromosomes,
                key=all_chromosomes.index)

    @classmethod
    def _arguments(cls):
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
        # arguments.append(CLIArgument(
        #     "--cnv-chrom",
        #     value_type=str,
        #     default_value="chrom",
        #     help_text="The label or index of the"
        #     " column containing the chromosome"
        #     " of the variant. [Default: chrom]",
        # ))
        # arguments.append(CLIArgument(
        #     "--cnv-start",
        #     value_type=str,
        #     default_value="pos",
        #     help_text="The label or index of the"
        #     " column containing the start"
        #     " of the CNV. [Default: pos]",
        # ))
        # arguments.append(CLIArgument(
        #     "--cnv-end",
        #     value_type=str,
        #     default_value="pos_end",
        #     help_text="The label or index of the"
        #     " column containing the end"
        #     " of the CNV variant. [Default: pos_end]",
        # ))
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

    def reset_regions(self, regions):
        super().reset_regions(regions)

        result = []
        for reg in self.regions:
            if reg is None:
                continue
            result.append(Region.from_str(reg))
        self.regions = result

    def _is_in_regions(self, summary_variant: SummaryVariant) -> bool:
        if len(self.regions) == 0:
            return True
        isin = [
            r.isin(  # type: ignore
                self._adjust_chrom_prefix(summary_variant.chrom),
                summary_variant.position
            )
            for r in self.regions
        ]
        return any(isin)

    def close(self):
        pass

    def _full_variants_iterator_impl(
        self
    ) -> Generator[Tuple[SummaryVariant, List[FamilyVariant]], None, None]:
        # pylint: disable=too-many-locals
        group = self.cnv_df.groupby(
            ["chrom", "position", "end_position", "variant_type"],
            sort=False).agg(list)

        for num_idx, (idx, values) in enumerate(group.iterrows()):

            chrom, position, end_position, variant_type = idx  # type: ignore
            position = int(position)
            end_position = int(end_position)
            summary_rec = {
                "chrom": chrom,
                "reference": None,
                "alternative": None,
                "position": position,
                "end_position": end_position,
                "summary_variant_index": num_idx,
                "variant_type": variant_type,
                "allele_index": 0
            }
            alt_rec = copy(summary_rec)
            del summary_rec["end_position"]
            del summary_rec["variant_type"]

            alt_rec["allele_index"] = 1

            svar = SummaryVariantFactory.summary_variant_from_records(
                [summary_rec, alt_rec], self.transmission_type
            )

            if not self._is_in_regions(svar):
                continue

            fvs = []
            extra_attributes_keys = filter(
                lambda x: x not in ["best_state", "family_id"],
                values.keys()
            )
            for f_idx, family_id in enumerate(
                    values.get("family_id")):  # type: ignore
                best_state = values.get("best_state")[f_idx]  # type: ignore
                family = self.families.get(family_id)
                if family is None:
                    continue
                fvar = FamilyVariant(svar, family, None, best_state)
                extra_attributes = {}
                for attr in extra_attributes_keys:
                    attr_val = values.get(attr)[f_idx]  # type: ignore
                    extra_attributes[attr] = [attr_val]
                fvar.update_attributes(extra_attributes)
                fvs.append(fvar)
            yield svar, fvs

    def full_variants_iterator(self):
        full_iterator = super().full_variants_iterator()

        for summary_variants, family_variants in full_iterator:
            for fvar in family_variants:
                for fallele in fvar.family_alt_alleles:
                    if self.transmission_type == TransmissionType.denovo:
                        inheritance = [
                            Inheritance.denovo if mem is not None else inh
                            for inh, mem in zip(
                                fallele.inheritance_in_members,
                                fallele.variant_in_members
                            )
                        ]
                        # pylint: disable=protected-access
                        fallele._inheritance_in_members = inheritance

            yield summary_variants, family_variants

    @classmethod
    def parse_cli_arguments(
        cls, argv: argparse.Namespace, use_defaults: bool = False
    ) -> Tuple[List[str], Dict[str, Any]]:
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
