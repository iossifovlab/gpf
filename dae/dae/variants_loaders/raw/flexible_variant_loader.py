from collections.abc import Callable, Generator, Sequence
from typing import Any, TextIO

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils.dae_utils import dae2vcf_variant
from dae.variants.variant import allele_type_from_cshl_variant


def location_variant_to_vcf_transformer(genome: ReferenceGenome) \
        -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a function extracting chrom,pos,ref,alt from a vcf variant."""
    def transformer(result: dict[str, Any]) -> dict[str, Any]:
        location: str = result["location"]
        variant: str = result["variant"]

        chrom, pos_part = location.split(":")
        cshl_pos = int(pos_part)

        pos, ref, alt = dae2vcf_variant(chrom, cshl_pos, variant, genome)

        result["chrom"] = chrom
        result["pos"] = pos
        result["ref"] = ref
        result["alt"] = alt

        return result

    return transformer


def variant_to_variant_type() -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a function extracting the variant type from a vcf variant."""
    def transformer(result: dict[str, Any]) -> dict[str, Any]:
        variant: str = result["variant"]

        variant_type = allele_type_from_cshl_variant(variant)
        result["variant_type"] = variant_type
        return result

    return transformer


def adjust_chrom_prefix(
    add_chrom_prefix: str | None = None,
    del_chrom_prefix: str | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a function that adds/removes a prefix to/from chrom names."""
    if add_chrom_prefix is not None:
        def _add_chrom_prefix(record: dict[str, Any]) -> dict[str, Any]:
            chrom = record["chrom"]
            if add_chrom_prefix not in chrom:
                record["chrom"] = f"{add_chrom_prefix}{chrom}"
            return record

        return _add_chrom_prefix

    if del_chrom_prefix is not None:
        def _del_chrom_prefix(record: dict[str, Any]) -> dict[str, Any]:
            chrom = record["chrom"]
            if del_chrom_prefix in chrom:
                record["chrom"] = chrom[len(del_chrom_prefix):]
            return record

        return _del_chrom_prefix

    def _identity(record: dict[str, Any]) -> dict[str, Any]:
        return record

    return _identity


def flexible_variant_loader(
    infile: TextIO,
    in_header: list[str],
    line_splitter: Callable,
    transformers: Sequence[Callable[[dict[str, Any]], dict[str, Any]]],
    filters: Sequence[Callable[[dict[str, Any]], bool]],
) -> Generator[dict[str, Any], None, None]:
    """Split,transform and filter each line from infile."""
    for line in infile:
        parts = line_splitter(line)
        assert len(in_header) == len(parts), (in_header, parts)
        result: dict[str, Any] = dict(zip(in_header, parts, strict=False))
        for transformer in transformers:
            result = transformer(result)
        if not all(f(result) for f in filters):
            continue
        yield result
