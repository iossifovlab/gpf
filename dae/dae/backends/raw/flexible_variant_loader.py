from dae.pedigrees.family import FamiliesData
import numpy as np

from typing import Callable, Generator, Dict, Any, Sequence, TextIO, Tuple

from dae.utils.dae_utils import dae2vcf_variant
from dae.utils.variant_utils import get_interval_locus_ploidy

from dae.variants.variant import allele_type_from_cshl_variant
from dae.variants.core import Allele

from dae.genomic_resources.reference_genome import ReferenceGenome


def location_variant_to_vcf_transformer(
        genome: ReferenceGenome) \
        -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def transformer(result: Dict[str, Any]) -> Dict[str, Any]:
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


def variant_to_variant_type() \
        -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    def transformer(result: Dict[str, Any]) -> Dict[str, Any]:
        variant: str = result["variant"]

        variant_type = allele_type_from_cshl_variant(variant)
        result["variant_type"] = variant_type
        return result

    return transformer


def cnv_location_to_vcf_trasformer() \
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


def cnv_dae_best_state_to_best_state(
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


def cnv_variant_to_variant_type(
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


def flexible_variant_loader(
        infile: TextIO,
        in_header: Tuple[str, ...],
        line_splitter: Callable,
        transformers: Sequence[Callable[[Dict[str, Any]], Dict[str, Any]]]) \
            -> Generator[Dict[str, Any], None, None]:

    for line in infile:
        parts = line_splitter(line)
        assert len(in_header) == len(parts), (in_header, parts)
        result: Dict[str, Any] = {
            k: v for k, v in zip(in_header, parts)
        }
        for transformer in transformers:
            result = transformer(result)
        yield result
