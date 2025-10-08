import logging

from dae.annotation.annotation_config import (
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
    build_gene_models_from_resource_id,
)
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)

logger = logging.getLogger(__name__)


def find_annotator_gene_models(
    info: AnnotatorInfo,
    grr: GenomicResourceRepo,
) -> GeneModels:
    """Get gene models from the annotator info or genomic context."""
    gene_models_resource_id = info.parameters.get("gene_models")
    if gene_models_resource_id is not None:
        logger.debug(
            "Gene models for %s taken from %s",
            info.type, gene_models_resource_id)
        return build_gene_models_from_resource_id(
            gene_models_resource_id, grr,
        )

    gene_models = get_genomic_context().get_gene_models()
    if gene_models is None:
        raise ValueError(
            f"Can't create {info.type}: "
            f"gene models resource is missing in config "
            f"and context")
    return gene_models


def find_annotator_reference_genome(
    info: AnnotatorInfo,
    gene_models: GeneModels,
    pipeline: AnnotationPipeline,
    grr: GenomicResourceRepo,
) -> ReferenceGenome:
    """Get reference genome from the annotator info or genomic context."""
    genome_resource_id = info.parameters.get("genome") or \
        gene_models.reference_genome_id or \
        (pipeline.preamble.input_reference_genome
            if pipeline.preamble is not None else None)

    genome: ReferenceGenome | None

    if genome_resource_id is not None:
        logger.debug(
            "Reference genome for %s taken from %s",
            info.type, genome_resource_id)
        return build_reference_genome_from_resource_id(
            genome_resource_id, grr)

    genome = get_genomic_context().get_reference_genome()
    if genome is None:
        raise ValueError(
            f"The {info} has no reference genome"
            " specified and no genome was found"
            " in the gene models' configuration,"
            " the context or the annotation config's"
            " preamble.")
    return genome
