from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict, Any, Tuple, Generator
from copy import copy
import numpy as np
import pandas as pd

from dae.genome.genomes_db import Genome
from dae.backends.raw.loader import VariantsGenotypesLoader, TransmissionType
from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import VariantType, Inheritance
from dae.variants.variant import SummaryVariantFactory, SummaryVariant
from dae.variants.family_variant import FamilyVariant

from dae.utils.regions import Region
from dae.utils.variant_utils import GENOTYPE_TYPE, get_interval_locus_ploidy


class CNVLoader(VariantsGenotypesLoader):
    def __init__(
            self,
            families: FamiliesData,
            cnv_filename: str,
            genome: Genome,
            regions: List[str] = None,
            params: Dict[str, Any] = {}):

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
            families,
            genome,
            adjust_chrom_prefix=self._adjust_chrom_prefix,
            **self.params,
        )

        self._init_chromosomes()

    def _init_chromosomes(self):
        self.chromosomes = list(self.cnv_df.chrom.unique())
        self.chromosomes = [
            self._adjust_chrom_prefix(chrom) for chrom in self.chromosomes
        ]

        all_chromosomes = self.genome.get_genomic_sequence().chromosomes
        if all([chrom in set(all_chromosomes) for chrom in self.chromosomes]):
            self.chromosomes = sorted(
                self.chromosomes,
                key=lambda chrom: all_chromosomes.index(chrom),
            )

    def reset_regions(self, regions):
        super(CNVLoader, self).reset_regions(regions)

        result = []
        for r in self.regions:
            if r is None:
                result.append(r)
            else:
                result.append(Region.from_str(r))
        self.regions = result
        print("CNV reset regions:", self.regions)

    def _is_in_regions(self, summary_variant: SummaryVariant) -> bool:
        isin = [
            r.isin(  # type: ignore
                summary_variant.chrom, summary_variant.position
            )
            if r is not None
            else True
            for r in self.regions
        ]
        return any(isin)

    def _full_variants_iterator_impl(
        self
    ) -> Generator[Tuple[SummaryVariant, List[FamilyVariant]], None, None]:

        for index, rec in enumerate(self.cnv_df.to_dict(orient="records")):
            family_id = rec.pop("family_id")
            best_state = rec.pop("best_state")
            rec["reference"] = None
            rec["alternative"] = None

            rec["position"] = int(rec["position"])
            rec["end_position"] = int(rec["end_position"])

            rec["summary_variant_index"] = index
            rec["allele_index"] = 0

            alt_rec = copy(rec)
            del rec["end_position"]
            del rec["variant_type"]

            alt_rec["allele_index"] = 1

            sv = SummaryVariantFactory.summary_variant_from_records(
                [rec, alt_rec], self.transmission_type
            )
            if not self._is_in_regions(sv):
                continue

            family = self.families.get(family_id)
            if family is None:
                continue

            fv = FamilyVariant(sv, family, None, best_state)

            yield sv, [fv]

    def full_variants_iterator(self):
        full_iterator = super(CNVLoader, self).full_variants_iterator()
        for summary_vairants, family_variants in full_iterator:
            for fv in family_variants:
                for fa in fv.alt_alleles:
                    inheritance = [
                        Inheritance.denovo if mem is not None else inh
                        for inh, mem in zip(
                            fa.inheritance_in_members, fa.variant_in_members
                        )
                    ]
                    fa._inheritance_in_members = inheritance

            yield summary_vairants, family_variants

    @classmethod
    def _calc_cnv_best_state(
        cls,
        best_state: str,
        variant_type: VariantType,
        expected_ploidy: np.ndarray,
    ) -> np.ndarray:
        actual_ploidy = np.fromstring(best_state, dtype=GENOTYPE_TYPE, sep=" ")
        if variant_type == VariantType.cnv_p:
            alt_row = actual_ploidy - expected_ploidy
        elif variant_type == VariantType.cnv_m:
            alt_row = expected_ploidy - actual_ploidy
        else:
            assert (
                False
            ), "Trying to generate CNV best state for non cnv variant"

        ref_row = expected_ploidy - alt_row
        return np.stack((ref_row, alt_row)).astype(np.int8)

    @classmethod
    def load_cnv(
            cls,
            filepath: str,
            families: FamiliesData,
            genome: Genome,
            cnv_location: Optional[str] = None,
            cnv_family_id: Optional[str] = None,
            cnv_variant_type: Optional[str] = None,
            cnv_best_state: Optional[str] = None,
            cnv_sep: str = "\t",
            adjust_chrom_prefix=None,
            **kwargs) -> pd.DataFrame:

        # TODO: Remove effect types when effect annotation is made
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
                # "effectType": str,
                # "effectGene": str,
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

        effect_genes_col = list(
            map(lambda x: x.split("|"), raw_df["effectGene"])
        )
        effect_gene_genes = []
        effect_gene_types = []
        for egs in effect_genes_col:
            effect_genes: List[Optional[str]] = []
            effect_types: List[Optional[str]] = []
            for eg in egs:
                split = eg.split(":")
                if len(split) == 1:
                    effect_genes.append(None)
                    effect_types.append(split[0])
                else:
                    effect_genes.append(split[0])
                    effect_types.append(split[1])
            effect_gene_genes.append(effect_genes)
            effect_gene_types.append(effect_types)

        def get_expected_ploidy(chrom, pos_start, pos_end, family_id):
            return np.asarray([
                get_interval_locus_ploidy(
                    chrom,
                    int(pos_start),
                    int(pos_end),
                    person.sex,
                    genome
                )
                for person in families[family_id].members_in_order
            ])

        expected_ploidy_col = tuple(
            map(
                lambda row: get_expected_ploidy(*row),
                zip(chrom_col, start_col, end_col, family_id_col),
            )
        )

        best_state_col = tuple(
            map(
                lambda x: cls._calc_cnv_best_state(*x),
                zip(
                    raw_df[cnv_best_state],
                    variant_type_col,
                    expected_ploidy_col,
                ),
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
                # "effect_type": raw_df["effectType"],
                # "effect_gene_genes": effect_gene_genes,
                # "effect_gene_types": effect_gene_types,
                # "effect_details_transcript_ids": [""] * len(chrom_col),
                # "effect_details_details": [""] * len(chrom_col),
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
            help="CNV file field separator. [Default: `\\t`]",
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
        cls, argv: Namespace
    ) -> Tuple[str, Dict[str, Any]]:
        return argv.cnv_file, \
            {
                "cnv_location": argv.cnv_location,
                "cnv_family_id": argv.cnv_family_id,
                "cnv_variant_type": argv.cnv_variant_type,
                "cnv_best_state": argv.cnv_best_state,
                "cnv_sep": argv.cnv_sep,
                "add_chrom_prefix": argv.add_chrom_prefix,
                "del_chrom_prefix": argv.del_chrom_prefix,
            }

    @classmethod
    def build_cli_arguments(cls, params):
        param_defaults = CNVLoader.cli_defaults()
        result = []
        for k, v in params.items():
            assert k in param_defaults, (k, list(param_defaults.keys()))
            if v != param_defaults[k]:
                param = k.replace("_", "-")
                result.append(f"--{param}")
                result.append(f"{v}")

        return " ".join(result)

    @classmethod
    def cli_defaults(cls):
        return {
            "cnv_location": "location",
            "cnv_family_id": "familyId",
            "cnv_variant_type": "variant",
            "cnv_best_state": "bestState",
            "cnv_sep": "\t",
            "add_chrom_prefix": None,
            "del_chrom_prefix": None,
        }
