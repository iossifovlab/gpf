from argparse import Namespace
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
from dae.backends.raw.loader import CLIArgument

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
        arguments.append(CLIArgument(
            "--cnv-family-id",
            value_type=str,
            default_value="familyId",
            help_text="The label or index of the"
            " column containing family's ID."
            " [Default: familyId]",
        ))
        arguments.append(CLIArgument(
            "--cnv-variant_type",
            value_type=str,
            default_value="variant",
            help_text="The label or index of the"
            " column containing the variant's"
            " type. [Default: variant]",
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
            "--cnv-plus-type-value",
            value_type=str,
            default_value="CNV+",
            help_text="The cnv+ value used in the columns containing"
            " the variant's type. [Default: CNV+]",
        ))
        arguments.append(CLIArgument(
            "--cnv-minus-type-value",
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
        return arguments

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
        for summary_variants, family_variants in full_iterator:
            for fv in family_variants:
                for fa in fv.alt_alleles:
                    inheritance = [
                        Inheritance.denovo if mem is not None else inh
                        for inh, mem in zip(
                            fa.inheritance_in_members, fa.variant_in_members
                        )
                    ]
                    fa._inheritance_in_members = inheritance

            yield summary_variants, family_variants

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
            cnv_chrom: Optional[str] = None,
            cnv_start: Optional[str] = None,
            cnv_end: Optional[str] = None,
            cnv_location: Optional[str] = None,
            cnv_person_id: Optional[str] = None,
            cnv_family_id: Optional[str] = None,
            cnv_best_state: Optional[str] = None,
            cnv_variant_type: Optional[str] = None,
            cnv_plus_values: List[str] = ["CNV+"],
            cnv_minus_values: List[str] = ["CNV-"],
            cnv_sep: str = "\t",
            adjust_chrom_prefix=None,
            **kwargs) -> pd.DataFrame:

        # TODO: Remove effect types when effect annotation is made
        assert families is not None
        assert isinstance(families, FamiliesData)

        if isinstance(cnv_plus_values, str):
            cnv_plus_values = [cnv_plus_values]
        if isinstance(cnv_minus_values, str):
            cnv_minus_values = [cnv_minus_values]
        if not cnv_location and not cnv_chrom:
            cnv_location = "location"
        if not cnv_variant_type:
            cnv_variant_type = "variant"
        if not cnv_person_id:
            if not cnv_best_state:
                cnv_best_state = "bestState"
            if not cnv_family_id:
                cnv_family_id = "familyId"

        dtype_dict = {
            cnv_variant_type: str,
        }
        if cnv_location:
            dtype_dict[cnv_location] = str
        else:
            dtype_dict[cnv_chrom] = str
            dtype_dict[cnv_start] = int
            dtype_dict[cnv_end] = int

        if cnv_person_id:
            dtype_dict[cnv_person_id] = str
        else:
            dtype_dict[cnv_family_id] = str
            dtype_dict[cnv_best_state] = str

        raw_df = pd.read_csv(
            filepath,
            sep=cnv_sep,
            dtype=dtype_dict
        )

        if cnv_location:
            location = raw_df[cnv_location]
            chrom_col, full_pos = zip(*map(lambda x: x.split(":"), location))
            start_col, end_col = zip(*map(lambda x: x.split("-"), full_pos))
        else:
            chrom_col = raw_df[cnv_chrom]
            start_col = raw_df[cnv_start]
            end_col = raw_df[cnv_end]

        if adjust_chrom_prefix is not None:
            chrom_col = tuple(map(adjust_chrom_prefix, chrom_col))

        def translate_variant_type(variant_type):
            if variant_type in cnv_plus_values:
                return "CNV+"
            if variant_type in cnv_minus_values:
                return "CNV-"
            return None

        variant_types_transformed = raw_df[cnv_variant_type].apply(
            translate_variant_type
        )
        variant_type_col = tuple(
            map(VariantType.from_name_cnv, variant_types_transformed)
        )

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

        if cnv_person_id:
            best_state_col = []
            family_id_col = []

            person_id_col = raw_df[cnv_person_id]
            for chrom, pos_start, pos_end, person_id in zip(
                    chrom_col, start_col, end_col, person_id_col):
                family_best_states = dict()
                person = families.persons.get(person_id)
                family_id = person.family_id
                family = families[family_id]
                members = family.members_in_order
                if family_id in family_best_states:
                    idx = person.index
                    ref = family_best_states[family_id][0]
                    alt = family_best_states[family_id][1]
                    ref[idx] = ref[idx] - 1
                    alt[idx] = alt[idx] + 1
                else:
                    ref = []
                    alt = []
                    for idx, member in enumerate(members):
                        ref.append(
                            get_interval_locus_ploidy(
                                chrom,
                                int(pos_start),
                                int(pos_end),
                                member.sex,
                                genome
                            )
                        )
                        alt.append(0)
                        if member.person_id == person_id:
                            ref[idx] = ref[idx] - 1
                            alt[idx] = alt[idx] + 1
                    family_best_states[family_id] = np.asarray(
                        [ref, alt], dtype=GENOTYPE_TYPE)

                best_state = family_best_states[family_id]
                best_state_col.append(best_state)
                family_id_col.append(family_id)

        else:
            family_id_col = raw_df[cnv_family_id]
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

        result = {
            "chrom": chrom_col,
            "position": start_col,
            "end_position": end_col,
            "variant_type": variant_type_col,
            "best_state": best_state_col,
            "family_id": family_id_col
        }

        return pd.DataFrame(result)

    @classmethod
    def parse_cli_arguments(
        cls, argv: Namespace
    ) -> Tuple[str, Dict[str, Any]]:
        return argv.cnv_file, \
            {
                "cnv_location": argv.cnv_location,
                "cnv_person_id": argv.cnv_person_id,
                "cnv_family_id": argv.cnv_family_id,
                "cnv_variant_type": argv.cnv_variant_type,
                "cnv_best_state": argv.cnv_best_state,
                "cnv_sep": argv.cnv_sep,
                "add_chrom_prefix": argv.add_chrom_prefix,
                "del_chrom_prefix": argv.del_chrom_prefix,
            }
