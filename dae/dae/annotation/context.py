from __future__ import annotations

import argparse
import logging
import pathlib

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.genomic_context import (
    CLIGenomicContext,
    GenomicContext,
    register_context,
)
from dae.genomic_resources.implementations.annotation_pipeline_impl import (
    AnnotationPipelineImplementation,
)

logger = logging.getLogger(__name__)


class CLIAnnotationContext(CLIGenomicContext):
    """Defines annotation pipeline genomics context."""

    @staticmethod
    def add_context_arguments(parser: argparse.ArgumentParser) -> None:
        """Add command line arguments to the argument parser."""
        parser.add_argument(
            "pipeline", default="context", nargs="?",
            help="The pipeline definition file. By default, or if "
            "the value is gpf_instance, the annotation pipeline "
            "from the configured gpf instance will be used.")
        parser.add_argument(
            "-ar", "--allow-repeated-attributes", default=False,
            action="store_true",
            help="Rename repeated attributes instead of raising"
            " an error.")
        CLIGenomicContext.add_context_arguments(parser)

    @staticmethod
    def context_builder(args: argparse.Namespace) -> CLIAnnotationContext:
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
            assert grr is not None

            pipeline_path = pathlib.Path(args.pipeline)
            pipeline_resource = grr.find_resource(args.pipeline)

            if pipeline_path.exists():
                raw_pipeline = pipeline_path.read_text()
            elif pipeline_resource is not None:
                raw_pipeline = AnnotationPipelineImplementation(
                   pipeline_resource).raw
            else:
                raise ValueError(
                    f"The provided argument for an annotation"
                    f" pipeline ('{args.pipeline}') is neither a valid"
                    f" filepath, nor a valid GRR resource ID.")

            work_dir = None
            if hasattr(args, "work_dir"):
                work_dir = pathlib.Path(args.work_dir)

            pipeline = load_pipeline_from_yaml(
                raw_pipeline, grr,
                allow_repeated_attributes=args.allow_repeated_attributes,
                work_dir=work_dir)
            context_objects["annotation_pipeline"] = pipeline

        return CLIAnnotationContext(
            context_objects, source=("CLIAnnotationContext", ))

    @staticmethod
    def register(args: argparse.Namespace) -> None:
        context = CLIAnnotationContext.context_builder(args)
        register_context(context)

    @staticmethod
    def get_pipeline(context: GenomicContext) -> AnnotationPipeline:
        """Construct an annotation pipeline."""
        pipeline = context.get_context_object("annotation_pipeline")
        if pipeline is None:
            raise ValueError(
                "Unable to find annotation pipeline in genomic context")
        if not isinstance(pipeline, AnnotationPipeline):
            raise TypeError(
                "The annotation pipeline from the genomic "
                " context is not an AnnotationPipeline")
        return pipeline
