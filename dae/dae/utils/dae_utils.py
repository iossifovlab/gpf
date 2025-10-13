import re
from collections.abc import Generator, Iterable
from typing import Any

from dae.genomic_resources.reference_genome import ReferenceGenome

SUB_COMPLEX_RE = re.compile(r"^(sub|complex|comp)\(([NACGT]+)->([NACGT]+)\)$")
INS_RE = re.compile(r"^ins\(([NACGT]+)\)$")
DEL_RE = re.compile(r"^del\((\d+)\)$")


def dae2vcf_variant(
    chrom: str, position: int, variant: str, genome: ReferenceGenome | None,
) -> tuple[int, str, str]:
    """Convert a given CSHL-style variant to the VCF format."""
    match = SUB_COMPLEX_RE.match(variant)
    if match:
        return position, match.group(2), match.group(3)
    if genome is None:
        raise ValueError("genome is required for ins/del variants")
    match = INS_RE.match(variant)
    if match:
        alt_suffix = match.group(1)
        reference = genome.get_sequence(chrom, position - 1, position - 1)
        return position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(variant)
    if match:
        count = int(match.group(1))
        reference = genome.get_sequence(
            chrom, position - 1, position + count - 1,
        )
        assert len(reference) == count + 1, reference
        return position - 1, reference, reference[0]

    raise NotImplementedError("weird variant: " + variant)


def cshl2vcf_variant(
    location: str, variant: str, genome: ReferenceGenome | None,
) -> tuple[str, int, str, str]:
    chrom, position = location.split(":")
    return chrom, *dae2vcf_variant(chrom, int(position), variant, genome)


def split_iterable(
    iterable: Iterable, max_chunk_length: int = 50,
) -> Generator[list, None, None]:
    """Split an iterable into chunks of a list type."""
    i = 0
    result = []

    for value in iterable:
        i += 1
        result.append(value)

        if i == max_chunk_length:
            yield result
            result = []
            i = 0

    if i != 0:
        yield result


def join_line(line: list[Any | list[Any]], sep: str = "\t") -> str:
    """Join an iterable representing a line into a string."""
    flattened_line = [
        "; ".join(v) if isinstance(v, list) else v
        for v in line]
    none_as_str_line = [
        "" if v is None or v == "None" else str(v)
        for v in flattened_line]
    return sep.join(none_as_str_line) + "\n"
