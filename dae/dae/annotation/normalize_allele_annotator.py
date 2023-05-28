"""Provides normalize allele annotator and helpers."""
import logging
from typing import Any

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.annotation_pipeline import AttributeInfo
from dae.genomic_resources.genomic_context import get_genomic_context

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotator_base import AnnotatorBase

logger = logging.getLogger(__name__)


def normalize_allele(allele: VCFAllele, genome: ReferenceGenome) -> VCFAllele:
    """Normalize an allele.

    Using algorithm defined in
    following https://genome.sph.umich.edu/wiki/Variant_Normalization
    """
    while True:
        changed = False
        logger.debug("normalizing allele: %s", allele)

        if len(allele.ref) > 0 and len(allele.alt) > 0 \
                and allele.ref[-1] == allele.alt[-1]:
            logger.debug("shrink from right: %s", allele)
            if allele.ref == allele.alt and len(allele.ref) == 1:
                logger.warning("no variant: %s", allele)
            else:
                allele = VCFAllele(
                    allele.chrom, allele.pos, allele.ref[:-1], allele.alt[:-1])
                changed = True

        if len(allele.ref) == 0 or len(allele.alt) == 0:
            logger.debug("moving left allele: %s", allele)
            left = genome.get_sequence(
                allele.chrom, allele.pos - 1, allele.pos - 1)
            allele = VCFAllele(
                allele.chrom, allele.pos - 1,
                f"{left}{allele.ref}", f"{left}{allele.alt}")
            changed = True

        if not changed:
            break

    while len(allele.ref) >= 2 and len(allele.alt) >= 2 \
            and allele.ref[0] == allele.alt[0]:
        allele = VCFAllele(
            allele.chrom, allele.pos + 1, allele.ref[1:], allele.alt[1:])

    return allele


def build_normalize_allele_annotator(pipeline: AnnotationPipeline,
                                     info: AnnotatorInfo) -> Annotator:
    return NormalizeAlleleAnnotator(pipeline, info)


class NormalizeAlleleAnnotator(AnnotatorBase):
    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        genome_resrouce_id = info.parameters.get("genome")
        if genome_resrouce_id is None:
            genome = get_genomic_context().get_reference_genome()
            if genome is None:
                raise ValueError("The {info}  has no reference genome "
                                 "specified and a genome is missing in "
                                 "the context.")
        else:
            resource = pipeline.repository.get_resource(genome_resrouce_id)
            genome = build_reference_genome_from_resource(resource)
        assert isinstance(genome, ReferenceGenome)

        info.resources += [genome.resource]
        if not info.attributes:
            info.attributes = [AttributeInfo("normalized_allele",
                                             "normalized_allele", True, {})]
        super().__init__(pipeline, info, {
            "normalized_allele": ("object", "Normalized allele.")
        })

        self.genome = genome

    def close(self):
        self.genome.close()
        super().close()

    def open(self):
        self.genome.open()
        return super().open()

    def _do_annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:
        if not isinstance(annotatable, VCFAllele):
            return {"normalized_allele": annotatable}

        assert isinstance(annotatable, VCFAllele), annotatable

        normalized_allele = normalize_allele(annotatable, self.genome)
        return {"normalized_allele": normalized_allele}
