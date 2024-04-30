"""Provides normalize allele annotator and helpers."""
import itertools
import logging
from typing import Any

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
    AttributeInfo,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)

logger = logging.getLogger(__name__)


def build_normalize_allele_annotator(pipeline: AnnotationPipeline,
                                     info: AnnotatorInfo) -> Annotator:
    return NormalizeAlleleAnnotator(pipeline, info)


class NormalizeAlleleAnnotator(AnnotatorBase):
    """Annotator to normalize VCF alleles."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        genome_resrouce_id = info.parameters.get("genome")
        if genome_resrouce_id is None:
            genome = get_genomic_context().get_reference_genome()
            if genome is None:
                raise ValueError(
                    f"The {info}  has no reference genome "
                    f"specified and a genome is missing in "
                    f"the context.")
        else:
            resource = pipeline.repository.get_resource(genome_resrouce_id)
            genome = build_reference_genome_from_resource(resource)
        assert isinstance(genome, ReferenceGenome)

        info.resources += [genome.resource]
        if not info.attributes:
            info.attributes = [
                AttributeInfo(
                    "normalized_allele",
                    "normalized_allele",
                    True,  # noqa FBT003
                    {})]
        super().__init__(pipeline, info, {
            "normalized_allele": ("annotatable", "Normalized allele."),
        })

        self.genome = genome

    def close(self) -> None:
        self.genome.close()
        super().close()

    def open(self) -> Annotator:
        self.genome.open()
        return super().open()

    def _do_annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:
        if not isinstance(annotatable, VCFAllele):
            return {"normalized_allele": annotatable}

        assert isinstance(annotatable, VCFAllele), annotatable

        normalized_allele = normalize_allele(annotatable, self.genome)
        return {"normalized_allele": normalized_allele}


def normalize_allele(allele: VCFAllele, genome: ReferenceGenome) -> VCFAllele:
    """Normalize an allele.

    Using algorithm defined in
    following https://genome.sph.umich.edu/wiki/Variant_Normalization
    """
    chrom, pos, ref, alts = normalize_variant(
        allele.chrom, allele.pos, allele.ref, [allele.alt], genome)
    return VCFAllele(chrom, pos, ref, alts[0])


def normalize_variant(
    chrom: str,
    pos: int,
    ref: str,
    alts: list[str],
    genome: ReferenceGenome,
) -> tuple[str, int, str, list[str]]:
    """Normalize a variant.

    Using algorithm defined in
    the https://genome.sph.umich.edu/wiki/Variant_Normalization
    """

    while True:
        changed = False
        logger.debug("normalizing variant: %s:%d %s>%s", chrom, pos, ref, alts)

        if len(ref) > 0 and all(len(alt) > 0
                and ref[-1] == alt[-1] for alt in alts):
            logger.debug(
                "shrink from right: %s:%d %s>%s", chrom, pos, ref, alts)
            if all(ref == alt for alt in alts) and len(ref) == 1:
                logger.info(
                    "no variant: %s:%d %s>%s", chrom, pos, ref, alts)
            else:
                ref = ref[:-1]
                alts = [alt[:-1] for alt in alts]
                changed = True

        if pos > 1 and (
                len(ref) == 0 or
                any(len(alt) == 0 for alt in alts)):
            logger.debug(
                "moving left variant: %s:%d %s>%s", chrom, pos, ref, alts)
            left = genome.get_sequence(
                chrom, pos - 1, pos - 1)
            pos -= 1
            ref = f"{left}{ref}"
            alts = [f"{left}{alt}" for alt in alts]
            changed = True

        if not changed:
            break

    while len(ref) >= 2 and all(len(alt) >= 2
            and ref[0] == alt[0] for alt in alts):
        pos += 1
        ref = ref[1:]
        alts = [alt[1:] for alt in alts]

    return chrom, pos, ref, alts


def maximally_extend_variant(
    chrom: str,
    pos: int,
    ref: str,
    alts: list[str],
    genome: ReferenceGenome,
) -> tuple[str, int, str, list[str]]:
    """Maximally extend a variant."""
    chrom, pos, ref, alts = normalize_variant(chrom, pos, ref, alts, genome)
    if not all(alt[0] == ref[0] for alt in alts):
        left = genome.get_sequence(chrom, pos - 1, pos - 1)
        pos -= 1
        ref = f"{left}{ref}"
        alts = [f"{left}{alt}" for alt in alts]
    if not all(alt[-1] == ref[-1] for alt in alts):
        right = genome.get_sequence(chrom, pos + len(ref), pos + len(ref))
        ref = f"{ref}{right}"
        alts = [f"{alt}{right}" for alt in alts]
    while True:
        changed = False
        for (s1, s2) in itertools.pairwise([ref, *alts]):
            if len(s1) > len(s2):
                s1, s2 = s2, s1
            if s2.startswith(s1) or s2.endswith(s1):
                right = genome.get_sequence(
                    chrom, pos + len(ref), pos + len(ref))
                ref = f"{ref}{right}"
                alts = [f"{alt}{right}" for alt in alts]
                changed = True
                break
        if not changed:
            break
    return chrom, pos, ref, alts
