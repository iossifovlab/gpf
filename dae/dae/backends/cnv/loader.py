from argparse import ArgumentParser
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd

from dae.GenomeAccess import GenomicSequence
from dae.backends.raw.loader import VariantsGenotypesLoader, TransmissionType
from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import VariantType
from dae.variants.variant import SummaryVariantFactory, SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.annotation.tools.file_io_parquet import ParquetSchema

from dae.RegionOperations import Region
from dae.utils.variant_utils import GENOTYPE_TYPE


class CNVLoader(VariantsGenotypesLoader):
    def __init__(
        self,
        families: FamiliesData,
        cnv_filename: str,
        genome: GenomicSequence,
        regions: List[str] = None,
        params: Dict[str, Any] = {},
    ):
        super(CNVLoader, self).__init__(
            families=families,
            filenames=[cnv_filename],
            transmission_type=TransmissionType.denovo,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=True,
            params=params,
        )

        self.genome = genome
        self.set_attribute("source_type", "cnv")

        self.cnv_df = self.load_cnv(
            cnv_filename,
            families=families,
            adjust_chrom_prefix=self._adjust_chrom_prefix,
            **self.params
        )

        self.regions = [Region.from_str(r) for r in self.regions]
        for region in self.regions:
            if region is None:
                continue
            region.chrom = self._adjust_chrom_prefix(region.chrom)

        self.annotation_schema = ParquetSchema.from_arrow(
            ParquetSchema.BASE_SCHEMA)
        self.set_attribute("annotation_schema", self.annotation_schema)

    def _is_in_regions(self, summary_variant: SummaryVariant) -> bool:
        isin = [
            r.isin(summary_variant.chrom, summary_variant.position)
            if r is not None
            else True
            for r in self.regions
        ]
        return any(isin)

    def _full_variants_iterator_impl(
        self,
    ) -> Tuple[SummaryVariant, List[FamilyVariant]]:
        for index, rec in enumerate(self.cnv_df.to_dict(orient="records")):
            family_id = rec.pop("family_id")
            best_state = rec.pop("best_state")
            rec["reference"] = None
            rec["alternative"] = None

            rec["position"] = int(rec["position"])
            rec["end_position"] = int(rec["end_position"])

            rec["summary_variant_index"] = index
            rec["allele_index"] = 0
            sv = SummaryVariantFactory.summary_variant_from_records(
                [rec], self.transmission_type
            )
            if not self._is_in_regions(sv):
                continue

            family = self.families.get(family_id)
            if family is None:
                continue

            fv = FamilyVariant(
                sv, family, None, best_state
            )

            yield sv, [fv]

    @classmethod
    def _calc_cnv_best_state(
        cls, best_state: str, variant_type: VariantType
    ) -> np.ndarray:
        ref_row = np.fromstring(best_state, dtype=GENOTYPE_TYPE, sep=" ")
        alt_row = np.zeros(len(ref_row), dtype=GENOTYPE_TYPE)
        if variant_type == VariantType.cnv_p:
            assert all(ref_row >= 2), ref_row
            alt_row[ref_row > 2] = 1
            ref_row[ref_row > 2] = 1
        elif variant_type == VariantType.cnv_m:
            assert all(ref_row <= 2), ref_row
            alt_row[ref_row < 2] = 1
        else:
            assert (
                False
            ), "Trying to generate CNV best state for non cnv variant"

        return np.stack((ref_row, alt_row))

    @classmethod
    def load_cnv(
        cls,
        filepath: str,
        families: FamiliesData,
        cnv_location: Optional[str] = None,
        cnv_family_id: Optional[str] = None,
        cnv_variant_type: Optional[str] = None,
        cnv_best_state: Optional[str] = None,
        cnv_sep: str = "\t",
        adjust_chrom_prefix=None,
        **kwargs
    ) -> pd.DataFrame:
        assert families is not None
        assert isinstance(families, FamiliesData)

        if not cnv_location:
            cnv_location = "location"
        if not cnv_family_id:
            cnv_family_id = "familyId"
        if not cnv_variant_type:
            cnv_variant_type = "variant"
        if not cnv_best_state:
            cnv_best_state = "bestState"

        raw_df = pd.read_csv(
            filepath,
            sep=cnv_sep,
            dtype={
                cnv_location: str,
                cnv_family_id: str,
                cnv_variant_type: str,
                cnv_best_state: str,
            },
        )

        location = raw_df[cnv_location]
        chrom_col, full_pos = zip(*map(lambda x: x.split(":"), location))
        start_col, end_col = zip(*map(lambda x: x.split("-"), full_pos))

        if adjust_chrom_prefix is not None:
            chrom_col = tuple(map(adjust_chrom_prefix, chrom_col))

        family_id_col = raw_df[cnv_family_id]

        variant_type_col = tuple(
            map(VariantType.from_name, raw_df[cnv_variant_type])
        )

        best_state_col = tuple(
            map(
                lambda x: cls._calc_cnv_best_state(x[0], x[1]),
                zip(raw_df[cnv_best_state], variant_type_col),
            )
        )

        return pd.DataFrame(
            {
                "chrom": chrom_col,
                "position": start_col,
                "end_position": end_col,
                "variant_type": variant_type_col,
                "family_id": family_id_col,
                "best_state": best_state_col,
            }
        )

    @classmethod
    def cli_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "cnv_file",
            type=str,
            metavar="<variants filename>",
            help="cnv variants file",
        )
        cls.cli_options(parser)

    @classmethod
    def cli_options(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--cnv-location",
            type=str,
            default="location",
            help="The label or index of the column containing the CSHL-style"
            " location of the variant. [Default: location]",
        )
        parser.add_argument(
            "--cnv-family-id",
            type=str,
            default="familyId",
            help="The label or index of the column containing family's ID."
            " [Default: familyId]",
        )
        parser.add_argument(
            "--cnv-variant_type",
            type=str,
            default="variant",
            help="The label or index of the column containing the variant's"
            " type. [Default: variant]",
        )
        parser.add_argument(
            "--cnv-best-state",
            type=str,
            default="bestState",
            help="The label or index of the column containing the variant's"
            " best state. [Default: bestState]",
        )
        parser.add_argument(
            "--cnv-sep",
            type=str,
            default="\t",
            help="CNV file field separator. [Default: `\\t`]"
        )
        parser.add_argument(
            "--add-chrom-prefix",
            type=str,
            default=None,
            help="Add specified prefix to each chromosome name in "
            "variants file",
        )
        parser.add_argument(
            "--del-chrom-prefix",
            type=str,
            default=None,
            help="Removes specified prefix from each chromosome name in "
            "variants file",
        )

    @classmethod
    def parse_cli_arguments(
        cls, argv: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        return argv.cnv_file, {
            "cnv_location": argv.cnv_location,
            "cnv_family_id": argv.cnv_family_id,
            "cnv_variant_type": argv.cnv_variant_type,
            "cnv_best_state": argv.cnv_best_state,
            "cnv_sep": argv.cnv_sep,
            'add_chrom_prefix': argv.add_chrom_prefix,
            'del_chrom_prefix': argv.del_chrom_prefix
        }

    @classmethod
    def cli_defaults(cls):
        return {
            "cnv_location": "location",
            "cnv_family_id": "familyId",
            "cnv_variant_type": "variant",
            "cnv_best_state": "bestState",
            "cnv_sep": "\t",
            'add_chrom_prefix': None,
            'del_chrom_prefix': None
        }
