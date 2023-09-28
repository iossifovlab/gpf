from __future__ import annotations

import logging
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.genomic_context import register_context

from dae.genomic_resources.genomic_context import CLIGenomicContext

logger = logging.getLogger(__name__)


class CLIAnnotationContext(CLIGenomicContext):
    """Defines annotation pipeline genomics context."""

    @staticmethod
    def context_builder(args) -> CLIAnnotationContext:
        """Build a CLI genomic context."""
        context = CLIGenomicContext.context_builder(args)
        register_context(context)
        context_objects = {}

        if hasattr(args, "pipeline") and \
                args.pipeline is not None and args.pipeline != "context":
            logger.info(
                "Using the annotation pipeline from the file %s.",
                args.pipeline)
            grr = context.get_genomic_resources_repository()
            pipeline = build_annotation_pipeline(
                pipeline_config_file=args.pipeline,
                grr_repository=grr,
                allow_repeated_attributes=args.allow_repeated_attributes)
            context_objects["annotation_pipeline"] = pipeline

        return CLIAnnotationContext(
            context_objects, source=("CLIAnnotationContext", ))

    @staticmethod
    def register(args):
        context = CLIAnnotationContext.context_builder(args)
        register_context(context)

    @staticmethod
    def get_pipeline(context) -> AnnotationPipeline:
        """Construct an annotation pipeline."""
        pipeline = context.get_context_object("annotation_pipeline")
        if pipeline is None:
            raise ValueError(
                "Unable to find annotation pipeline in genomic context")
        if not isinstance(pipeline, AnnotationPipeline):
            raise ValueError(
                "The annotation pipeline from the genomic "
                " context is not an AnnotationPipeline")
        return pipeline
