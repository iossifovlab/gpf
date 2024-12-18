from collections.abc import Callable, Generator
from copy import deepcopy
from pathlib import Path
from typing import Any, TextIO

import numpy as np

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.utils.variant_utils import get_interval_locus_ploidy
from dae.variants.core import Allele
from dae.variants_loaders.raw.flexible_variant_loader import (
    flexible_variant_loader,
)


def _cnv_location_to_vcf_trasformer() \
        -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Expand shorthand loc notation to separate crom, pos, pos_end attrs.

    In case the input uses CNV location this transformer will produce
    internal (chrom, pos, pos_end) description of the CNV position.
    """
    def transformer(result: dict[str, Any]) -> dict[str, Any]:
        location = result["location"]
        chrom, pos_range = location.split(":")
        beg, end = pos_range.split("-")
        result["chrom"] = chrom
        result["pos"] = int(beg)
        result["pos_end"] = int(end)

        return result

    return transformer


def _cnv_vcf_to_vcf_trasformer() \
        -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Convert pos and pos_end to int.

    In case the input uses VCF-like description of the CNVs this
    transformer will check it and handle the proper type conversion for
    `pos` and `pos_end` values.
    """
    def trasformer(result: dict[str, Any]) -> dict[str, Any]:
        chrom = result["chrom"]
        pos = int(result["pos"])
        pos_end = int(result["pos_end"])

        result["chrom"] = chrom
        result["pos"] = pos
        result["pos_end"] = pos_end

        return result

    return trasformer


def _configure_cnv_location(
        header: list[str],
        transformers: list[Callable[[dict[str, Any]], dict[str, Any]]],
        cnv_chrom: str | None = None,
        cnv_start: str | None = None,
        cnv_end: str | None = None,
        cnv_location: str | None = None) -> None:
    """Configure the header and position-handling transformers.

    This helper function will **configure** the header and transformers needed
    to handle position of CNVs in the input record.
    """
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

        header[chrom_index] = "chrom"
        header[start_index] = "pos"
        header[end_index] = "pos_end"
        transformers.append(_cnv_vcf_to_vcf_trasformer())
    else:
        if cnv_location is None:
            cnv_location = "location"
        location_index = header.index(cnv_location)
        header[location_index] = "location"
        transformers.append(_cnv_location_to_vcf_trasformer())


def _cnv_dae_best_state_to_best_state(
        families: FamiliesData, genome: ReferenceGenome) \
        -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Transform old dae family id/best state to canonical form.

    In case the genotype of the CNVs is specified in old
    dae family id/best state notation, this transformer will handle it
    and transform it to canonical family id/best state form
    """
    def transformer(result: dict[str, Any]) -> dict[str, Any]:
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
                chrom, pos, pos_end, p.sex, genome,
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
        -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Transform variant into canonical family id/best state form.

    In case the genotype is specified by person id having the variant
    this transformer will transform it into canonical family id/best state
    form
    """
    def transformer(result: dict[str, Any]) -> dict[str, Any]:
        person_id = result["person_id"]
        if "family_id" in result:
            family_id = result["family_id"]
            family = families[family_id]
            person = family.persons[person_id]
            persons = [person]
        else:
            persons = []
            family_ids = set()
            for pid in person_id.split(";"):
                assert len(families.persons_by_person_id[pid]) == 1, pid
                person = families.persons_by_person_id[pid][0]
                persons.append(person)
                family_ids.add(person.family_id)
            assert len(family_ids) == 1, family_ids
            family = families[next(iter(family_ids))]

        chrom = result["chrom"]
        pos = result["pos"]
        pos_end = result["pos_end"]

        expected_ploidy = np.asarray([
            get_interval_locus_ploidy(
                chrom, pos, pos_end, p.sex, genome,
            ) for p in family.members_in_order
        ])
        alt_row = np.zeros(len(family.members_in_order), dtype=np.int8)
        for person in persons:
            alt_row[person.member_index] = 1

        ref_row = expected_ploidy - alt_row
        best_state = np.stack((ref_row, alt_row)).astype(np.int8)
        result["best_state"] = best_state
        result["family_id"] = family.family_id

        return result

    return transformer


def _configure_cnv_best_state(
        header: list[str],
        transformers: list[Callable[[dict[str, Any]], dict[str, Any]]],
        families: FamiliesData,
        genome: ReferenceGenome,
        cnv_person_id: str | None = None,
        cnv_family_id: str | None = None,
        cnv_best_state: str | None = None) -> None:
    """Configure header and transformers that handle CNV family genotypes."""
    if cnv_person_id is not None:
        person_index = header.index(cnv_person_id)
        header[person_index] = "person_id"

        transformers.append(
            _cnv_person_id_to_best_state(families, genome),
        )
    else:
        if cnv_family_id is None:
            cnv_family_id = "family_id"
        if cnv_best_state is None:
            cnv_best_state = "best_state"

        family_index = header.index(cnv_family_id)
        best_state_index = header.index(cnv_best_state)

        header[family_index] = "family_id"
        header[best_state_index] = "best_state"

        transformers.append(
            _cnv_dae_best_state_to_best_state(families, genome))


def _cnv_variant_to_variant_type(
    cnv_plus_values: list[str] | None = None,
    cnv_minus_values: list[str] | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Transform variant type to canonical internal representation.

    This transformer is used to transform variant type to canonical
    inernal representation using :class:`Allele.Type.large_duplication` and
    :class:`Allele.Type.large_deletion`.
    """
    if cnv_minus_values is None:
        cnv_minus_values = ["CNV-"]
    if cnv_plus_values is None:
        cnv_plus_values = ["CNV+"]

    def transformer(result: dict[str, Any]) -> dict[str, Any]:
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
    header: list[str],
    transformers: list[Callable[[dict[str, Any]], dict[str, Any]]],
    cnv_variant_type: str | None = None,
    cnv_plus_values: str | list[str] | None = None,
    cnv_minus_values: str | list[str] | None = None,
) -> None:
    """Configure header and transformer needed to handle CNV variant type."""
    if cnv_plus_values is None:
        cnv_plus_values = ["CNV+"]
    elif isinstance(cnv_plus_values, str):
        cnv_plus_values = [cnv_plus_values]

    if cnv_minus_values is None:
        cnv_minus_values = ["CNV-"]
    if isinstance(cnv_minus_values, str):
        cnv_minus_values = [cnv_minus_values]

    if cnv_variant_type is None:
        cnv_variant_type = "variant"

    variant_type_index = header.index(cnv_variant_type)
    header[variant_type_index] = "variant"

    transformers.append(
        _cnv_variant_to_variant_type(cnv_plus_values, cnv_minus_values),
    )


def _configure_loader(
        header: list[str],
        families: FamiliesData,
        genome: ReferenceGenome,
        cnv_chrom: str | None = None,
        cnv_start: str | None = None,
        cnv_end: str | None = None,
        cnv_location: str | None = None,
        cnv_person_id: str | None = None,
        cnv_family_id: str | None = None,
        cnv_best_state: str | None = None,
        cnv_variant_type: str | None = None,
        cnv_plus_values: list[str] | None = None,
        cnv_minus_values: list[str] | None = None) \
        -> tuple[
            list[str],
            list[Callable[[dict[str, Any]], dict[str, Any]]]]:
    """Configure all headers and transformers needed to handle CNVs input."""
    # pylint: disable=too-many-arguments
    transformers: list[
        Callable[[dict[str, Any]], dict[str, Any]]] = []
    header = deepcopy(header)

    _configure_cnv_location(
        header, transformers,
        cnv_chrom, cnv_start, cnv_end,
        cnv_location,
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


def flexible_cnv_loader(
    filepath_or_buffer: str | Path | TextIO,
    families: FamiliesData,
    genome: ReferenceGenome,
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
    **_kwargs: Any,
) -> Generator[dict[str, Any], None, None]:
    """Load variants from CNVs input and transform them into DataFrames.

    This function uses flexible variant loader infrastructure to
    load variants from a CNVs data input and transform them into a pandas
    `DataFrame`.
    """
    # pylint: disable=too-many-locals,too-many-arguments
    def line_splitter(line: str) -> list[str]:
        return line.strip("\n\r").split(cnv_sep)

    if isinstance(filepath_or_buffer, (str, Path)):
        infile = open(filepath_or_buffer, "rt")  # noqa: SIM115
    else:
        infile = filepath_or_buffer  # type: ignore

    with infile as infile:
        line = next(infile)  # pylint: disable=stop-iteration-return
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

        variant_generator = flexible_variant_loader(
            infile, header, line_splitter, transformers,
            filters=[],
        )

        yield from variant_generator
