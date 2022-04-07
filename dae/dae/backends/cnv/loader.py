import logging
import argparse
from pathlib import Path

from typing import Callable, List, Optional, Dict, Any, Tuple, Generator, \
    Union, TextIO, cast

from copy import copy, deepcopy
from dae.backends.raw.flexible_variant_loader import adjust_chrom_prefix, \
    flexible_variant_loader
import numpy as np
import pandas as pd

from dae.variants.core import Allele
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.backends.raw.loader import VariantsGenotypesLoader, TransmissionType

from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Inheritance
from dae.variants.variant import SummaryVariantFactory, SummaryVariant, \
    SummaryAllele, allele_type_from_name
from dae.variants.family_variant import FamilyVariant
from dae.backends.raw.loader import CLIArgument

from dae.utils.regions import Region
from dae.utils.variant_utils import GENOTYPE_TYPE, get_interval_locus_ploidy


logger = logging.getLogger(__name__)


def _cnv_location_to_vcf_trasformer() \
        -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def trasformer(result: Dict[str, Any]) -> Dict[str, Any]:
        location = result["location"]
        chrom, range = location.split(":")
        beg, end = range.split("-")
        result["chrom"] = chrom
        result["pos"] = int(beg)
        result["pos_end"] = int(end)

        return result

    return trasformer


def _cnv_vcf_to_vcf_trasformer() \
        -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def trasformer(result: Dict[str, Any]) -> Dict[str, Any]:
        chrom = result["chrom"]
        pos = int(result["pos"])
        pos_end = int(result["pos_end"])

        result["chrom"] = chrom
        result["pos"] = pos
        result["pos_end"] = pos_end

        return result

    return trasformer


def _configure_cnv_location(
        header: List[str],
        transformers: List[Callable[[Dict[str, Any]], Dict[str, Any]]],
        cnv_chrom: Optional[str] = None,
        cnv_start: Optional[str] = None,
        cnv_end: Optional[str] = None,
        cnv_location: Optional[str] = None) -> None:

    if cnv_chrom is not None or cnv_start is not None or \
            cnv_end is not None:
        if cnv_location is not None:
            raise ValueError(
                f"mixed variant location definitions: "
                f"vcf({cnv_chrom}:{cnv_start}-{cnv_end}) and "
                f"location({cnv_location})")
        if cnv_chrom is None:
            cnv_chrom = "chrom"
        if cnv_start is None:
            cnv_start = "pos"
        if cnv_end is None:
            cnv_end = "pos_end"
        
        chrom_index = header.index(cnv_chrom)
        start_index = header.index(cnv_start)
        end_index = header.index(cnv_end)

        if chrom_index == -1 or start_index == -1 or end_index == -1:
            raise ValueError(
                f"cant find cnv vcf position like columns "
                f"vcf({cnv_chrom}:{cnv_start}-{cnv_end}) in header: "
                f"{header}"
            )
        header[chrom_index] = "chrom"
        header[start_index] = "pos"
        header[end_index] = "pos_end"
        transformers.append(_cnv_vcf_to_vcf_trasformer())
    else:
        if cnv_location is None:
            cnv_location = "location"
        location_index = header.index(cnv_location)
        if location_index == -1:
            raise ValueError(
                f"can find cnv location column "
                f"location({cnv_location}) in header: "
                f"{header}"
            )
        header[location_index] = "location"
        transformers.append(_cnv_location_to_vcf_trasformer())


def _cnv_dae_best_state_to_best_state(
        families: FamiliesData, genome: ReferenceGenome) \
        -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def transformer(result: Dict[str, Any]) -> Dict[str, Any]:
        variant_type = result["variant_type"]
        actual_ploidy = np.fromstring(
            result["best_state"], dtype=np.int8, sep=" ")
        family_id = result["family_id"]
        family = families[family_id]
        chrom = result["chrom"]
        pos = result["pos"]
        pos_end = result["pos_end"]

        expected_ploidy = np.asarray([
            get_interval_locus_ploidy(
                chrom, pos, pos_end, p.sex, genome
            ) for p in family.members_in_order
        ])
        if variant_type == Allele.Type.large_duplication:
            alt_row = actual_ploidy - expected_ploidy
        elif variant_type == Allele.Type.large_deletion:
            alt_row = expected_ploidy - actual_ploidy
        else:
            raise ValueError(
                f"unexpected variant type: {variant_type}")
        ref_row = expected_ploidy - alt_row
        best_state = np.stack((ref_row, alt_row)).astype(np.int8)
        result["best_state"] = best_state

        return result

    return transformer


def _cnv_person_id_to_best_state(
        families: FamiliesData, genome: ReferenceGenome) \
        -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def transformer(result: Dict[str, Any]) -> Dict[str, Any]:
        person_id = result["person_id"]
        person = families.persons[person_id]
        family = families[person.family_id]

        chrom = result["chrom"]
        pos = result["pos"]
        pos_end = result["pos_end"]

        expected_ploidy = np.asarray([
            get_interval_locus_ploidy(
                chrom, pos, pos_end, p.sex, genome
            ) for p in family.members_in_order
        ])
        alt_row = np.zeros(len(family.members_in_order), dtype=np.int8)
        alt_row[person.index] = 1

        ref_row = expected_ploidy - alt_row
        best_state = np.stack((ref_row, alt_row)).astype(np.int8)
        result["best_state"] = best_state
        result["family_id"] = family.family_id

        return result

    return transformer


def _configure_cnv_best_state(
        header: List[str],
        transformers: List[Callable[[Dict[str, Any]], Dict[str, Any]]],
        families: FamiliesData,
        genome: ReferenceGenome,
        cnv_person_id: Optional[str] = None,
        cnv_family_id: Optional[str] = None,
        cnv_best_state: Optional[str] = None) -> None:

    if cnv_person_id is not None:
        if cnv_family_id is not None or cnv_best_state is not None:
            raise ValueError(
                f"mixed configuration of cnv best state: "
                f"person_id({cnv_person_id}) <-> "
                f"family_id({cnv_family_id}) and "
                f"best_state({cnv_best_state})"
            )
        person_index = header.index(cnv_person_id)
        if person_index == -1:
            raise ValueError(
                f"cant find person_id({cnv_person_id}) in header: "
                f"{header}")

        header[person_index] = "person_id"

        transformers.append(
            _cnv_person_id_to_best_state(families, genome)
        )
    else:
        if cnv_family_id is None:
            cnv_family_id = "family_id"
        if cnv_best_state is None:
            cnv_best_state = "best_state"
        family_index = header.index(cnv_family_id)
        best_state_index = header.index(cnv_best_state)
        if family_index == -1 or best_state_index == -1:
            raise ValueError(
                f"cant find family_id({cnv_family_id}) or "
                f"best_state({cnv_best_state}) in header: "
                f"{header}")
        header[family_index] = "family_id"
        header[best_state_index] = "best_state"

        transformers.append(
            _cnv_dae_best_state_to_best_state(families, genome))


def _cnv_variant_to_variant_type(
        cnv_plus_values=set(["CNV+"]),
        cnv_minus_values=set(["CNV-"])) \
            -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def transformer(result: Dict[str, Any]) -> Dict[str, Any]:
        variant = result["variant"]
        if variant in cnv_plus_values:
            variant_type = Allele.Type.large_duplication
        elif variant in cnv_minus_values:
            variant_type = Allele.Type.large_deletion
        else:
            raise ValueError(f"unexpected CNV variant type: {variant}")

        result["variant_type"] = variant_type
        return result

    return transformer


def _configure_cnv_variant_type(
        header: List[str],
        transformers: List[Callable[[Dict[str, Any]], Dict[str, Any]]],
        cnv_variant_type: Optional[str] = None,
        cnv_plus_values: Union[str, List[str]] = ["CNV+"],
        cnv_minus_values: Union[str, List[str]] = ["CNV-"]):

    if isinstance(cnv_plus_values, str):
        cnv_plus_values = [cnv_plus_values]
    if isinstance(cnv_minus_values, str):
        cnv_minus_values = [cnv_minus_values]

    if cnv_variant_type is None:
        cnv_variant_type = "variant"

    variant_type_index = header.index(cnv_variant_type)
    if variant_type_index == -1:
        raise ValueError(
            f"missing variant type column {cnv_variant_type} in header: "
            f"{header}")
    header[variant_type_index] = "variant"

    transformers.append(
        _cnv_variant_to_variant_type(cnv_plus_values, cnv_minus_values)
    )


def _configure_loader(
        header: List[str],
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
        cnv_plus_values: List[str] = ["CNV+"],
        cnv_minus_values: List[str] = ["CNV-"]) \
        -> Tuple[
            List[str], 
            List[Callable[[Dict[str, Any]], Dict[str, Any]]]]:

    transformers: List[
        Callable[[Dict[str, Any]], Dict[str, Any]]] = []
    header = deepcopy(header)

    _configure_cnv_location(
        header, transformers,
        cnv_chrom, cnv_start, cnv_end,
        cnv_location
    )

    _configure_cnv_variant_type(
        header, transformers,
        cnv_variant_type, cnv_plus_values, cnv_minus_values)

    _configure_cnv_best_state(
        header, transformers,
        families, genome,
        cnv_person_id,
        cnv_family_id, cnv_best_state)

    return header, transformers


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
        cnv_plus_values: List[str] = ["CNV+"],
        cnv_minus_values: List[str] = ["CNV-"],
        cnv_sep: str = "\t",
        add_chrom_prefix: Optional[str] = None,
        del_chrom_prefix: Optional[str] = None,
        **kwargs) -> pd.DataFrame:

    if isinstance(filepath_or_buffer, str) or \
            isinstance(filepath_or_buffer, Path):
        infile = open(filepath_or_buffer, "rt")
    else:
        infile = filepath_or_buffer

    def line_splitter(ln: str) -> List[str]:
        return ln.strip("\n\r").split(cnv_sep)

    with infile as infile:
        line = next(infile)
        header = line_splitter(line)

        header, transformers = _configure_loader(
            header,
            families,
            genome,
            cnv_chrom,
            cnv_start,
            cnv_end,
            cnv_location,
            cnv_person_id,
            cnv_family_id,
            cnv_best_state,
            cnv_variant_type,
            cnv_plus_values,
            cnv_minus_values)

        transformers.append(adjust_chrom_prefix(
            add_chrom_prefix, del_chrom_prefix))

        variant_generator = flexible_variant_loader(
                infile, header, line_splitter, transformers)

        data = []
        for record in variant_generator:
            print(record)
            data.append(record)

        df: pd.DataFarme = cast(
            pd.DataFrame,
            pd.DataFrame.from_records(  # type: ignore
                data, columns=[
                    "chrom", "pos", "pos_end",
                    "variant_type",
                    "family_id", "best_state"
                ]))

        df = df.rename(
            columns={
                "pos": "position", 
                "pos_end": "end_position"
            })
        return cast(pd.DataFrame, df)


class CNVLoader(VariantsGenotypesLoader):
    def __init__(
            self,
            families: FamiliesData,
            cnv_filename: str,
            genome: ReferenceGenome,
            regions: List[str] = None,
            params: Dict[str, Any] = None):

        if params is None:
            params = {}
        if params.get("cnv_transmission_type") == "denovo":
            transmission_type = TransmissionType.denovo
        else:
            transmission_type = TransmissionType.transmitted

        super(CNVLoader, self).__init__(
            families=families,
            filenames=[cnv_filename],
            transmission_type=transmission_type,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=True,
            params=params,
        )

        logger.info(f"CNV loader params: {params}")
        self.genome = genome
        self.set_attribute("source_type", "cnv")

        logger.info(f"CNV loader params: {self.params}")
        self.cnv_df = _cnv_loader(
            cnv_filename,
            families,
            genome,
            **self.params,
        )

        self._init_chromosomes()

    def _init_chromosomes(self):
        self.chromosomes = list(self.cnv_df.chrom.unique())

        all_chromosomes = self.genome.chromosomes
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
            "--cnv-variant-type",
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

        print(self.cnv_df)
        print(self.cnv_df.columns)

        group = self.cnv_df.groupby(
            ["chrom", "position", "end_position", "variant_type"],
            sort=False).agg(
                lambda x: list(x)
            )
        for num_idx, (idx, values) in enumerate(group.iterrows()):

            print(num_idx, idx, values)

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

            sv = SummaryVariantFactory.summary_variant_from_records(
                [summary_rec, alt_rec], self.transmission_type
            )

            if not self._is_in_regions(sv):
                continue

            fvs = []
            extra_attributes_keys = filter(
                lambda x: x not in ["best_state", "family_id"],
                values.keys()
            )
            for f_idx, family_id in enumerate(values.get("family_id")):
                best_state = values.get("best_state")[f_idx]
                family = self.families.get(family_id)
                if family is None:
                    continue
                fv = FamilyVariant(sv, family, None, best_state)
                extra_attributes = {}
                for attr in extra_attributes_keys:
                    attr_val = values.get(attr)[f_idx]
                    extra_attributes[attr] = [attr_val]
                fv.update_attributes(extra_attributes)
                fvs.append(fv)
            yield sv, fvs

    def full_variants_iterator(self):
        full_iterator = super(CNVLoader, self).full_variants_iterator()

        for summary_variants, family_variants in full_iterator:
            for fv in family_variants:
                for fa in fv.alt_alleles:
                    if self.transmission_type == TransmissionType.denovo:
                        inheritance = [
                            Inheritance.denovo if mem is not None else inh
                            for inh, mem in zip(
                                fa.inheritance_in_members,
                                fa.variant_in_members
                            )
                        ]
                        fa._inheritance_in_members = inheritance

            yield summary_variants, family_variants

    @classmethod
    def _calc_cnv_best_state(
        cls,
        best_state: str,
        variant_type: SummaryAllele.Type,
        expected_ploidy: np.ndarray,
    ) -> np.ndarray:
        actual_ploidy = np.fromstring(best_state, dtype=GENOTYPE_TYPE, sep=" ")
        if variant_type == SummaryAllele.Type.large_duplication:
            alt_row = actual_ploidy - expected_ploidy
        elif variant_type == SummaryAllele.Type.large_deletion:
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
            genome: ReferenceGenome,
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

        dtype_dict: Dict[str, Any] = {
            cnv_variant_type: str,
        }
        if cnv_location:
            dtype_dict[cnv_location] = str
        else:
            assert cnv_chrom is not None and cnv_start is not None and \
                cnv_end is not None

            dtype_dict[cnv_chrom] = str
            dtype_dict[cnv_start] = int
            dtype_dict[cnv_end] = int

        if cnv_person_id:
            dtype_dict[cnv_person_id] = str
        else:
            assert cnv_family_id is not None and cnv_best_state is not None

            dtype_dict[cnv_family_id] = str
            dtype_dict[cnv_best_state] = str

        raw_df = pd.read_csv(
            filepath,
            sep=cnv_sep,
            dtype=dtype_dict
        )

        if cnv_location:
            location: pd.Series = raw_df[cnv_location]

            def location_split(v: str) -> Tuple[str, ...]:
                return tuple(v.split(":"))

            chrom_col_data, full_pos_data = \
                zip(*map(location_split, location))
            chrom_col: pd.Series = pd.Series(
                index=raw_df.index, data=list(chrom_col_data))

            def range_split(v: str) -> Tuple[str, ...]:
                return tuple(v.split("-"))

            start_col_data, end_col_data = zip(
                *map(range_split, full_pos_data))

            start_col: pd.Series = pd.Series(
                index=raw_df.index, data=list(start_col_data))
            end_col: pd.Series = pd.Series(
                index=raw_df.index, data=list(end_col_data))

        else:
            assert cnv_chrom is not None and cnv_start is not None and \
                cnv_end is not None

            chrom_col = raw_df[cnv_chrom]
            start_col = raw_df[cnv_start]
            end_col = raw_df[cnv_end]

        if adjust_chrom_prefix is not None:
            chrom_col = chrom_col.apply(adjust_chrom_prefix)

        def translate_variant_type(variant_type):
            if variant_type in cnv_plus_values:
                return "CNV+"
            if variant_type in cnv_minus_values:
                return "CNV-"
            else:
                logger.error(f"unexpected CNV variant type: {variant_type}")
            return None

        variant_types_transformed = raw_df[cnv_variant_type].apply(
            translate_variant_type
        )
        variant_type_col = \
            variant_types_transformed.apply(allele_type_from_name)

        if cnv_person_id:
            best_state_col_data = []
            family_id_col_data = []
            variant_best_states: Dict[Tuple[Any, ...], np.ndarray] = dict()

            person_id_col = raw_df[cnv_person_id]
            for chrom, pos_start, pos_end, variant_type, person_id in zip(
                    chrom_col, start_col, end_col,
                    variant_type_col, person_id_col):

                person = families.persons.get(person_id)
                family_id = person.family_id
                family = families[family_id]
                members = family.members_in_order

                variant_index = (
                    chrom, pos_start, pos_end, variant_type, family_id
                )
                if variant_index in variant_best_states:
                    idx = person.index
                    ref = variant_best_states[variant_index][0]
                    alt = variant_best_states[variant_index][1]
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
                    variant_best_states[variant_index] = np.asarray(
                        [ref, alt], dtype=GENOTYPE_TYPE)

                best_state = variant_best_states[variant_index]
                best_state_col_data.append(best_state)
                family_id_col_data.append(family_id)
            family_id_col = pd.Series(family_id_col_data, index=raw_df.index)
            best_state_col = pd.Series(best_state_col_data, index=raw_df.index)

        else:

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

            assert cnv_family_id is not None
            family_id_col = raw_df[cnv_family_id]
            expected_ploidy_col = tuple(
                map(
                    lambda row: get_expected_ploidy(*row),
                    zip(chrom_col, start_col, end_col, family_id_col),
                )
            )
            assert cnv_best_state is not None

            best_state_col_data = \
                list(map(
                    lambda x: cls._calc_cnv_best_state(*x),
                    zip(
                        raw_df[cnv_best_state],
                        variant_type_col,
                        expected_ploidy_col,
                    ),
                ))
            best_state_col = pd.Series(best_state_col_data, index=raw_df.index)

        result: Dict[str, pd._ListLike] = {
            "chrom": chrom_col,
            "position": start_col,
            "end_position": end_col,
            "variant_type": variant_type_col,
            "best_state": best_state_col,
            "family_id": family_id_col
        }

        return pd.DataFrame(data=result)

    @classmethod
    def parse_cli_arguments(
        cls, argv: argparse.Namespace, use_defaults: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        return argv.cnv_file, \
            {
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
