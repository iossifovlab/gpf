"""Provides normalize allele annotator and helpers."""
import logging
from typing import Any

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.variant_utils import normalize_variant

logger = logging.getLogger(__name__)


def build_normalize_allele_annotator(pipeline: AnnotationPipeline,
                                     info: AnnotatorInfo) -> Annotator:
    return NormalizeAlleleAnnotator(pipeline, info)


class NormalizeAlleleAnnotator(AnnotatorBase):
    """Annotator to normalize VCF alleles."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        genome_resource_id = info.parameters.get("genome") or \
            (pipeline.preamble.input_reference_genome
             if pipeline.preamble is not None else None)
        if genome_resource_id is None:
            genome = get_genomic_context().get_reference_genome()
            if genome is None:
                raise ValueError(
                    f"The {info}  has no reference genome "
                    f"specified and a genome is missing in "
                    f"the context.")
        else:
            resource = pipeline.repository.get_resource(genome_resource_id)
            genome = build_reference_genome_from_resource(resource)
        assert isinstance(genome, ReferenceGenome)

        info.resources += [genome.resource]
        if not info.attributes:
            info.attributes = [
                AttributeInfo(
                    "normalized_allele",
                    "normalized_allele",
                    internal=True,
                    parameters={})]
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

    def _do_annotate(
        self, annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
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
