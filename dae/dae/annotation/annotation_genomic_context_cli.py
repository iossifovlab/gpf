from __future__ import annotations

import argparse
import logging
import pathlib
from typing import Any

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.genomic_context_base import (
    GC_ANNOTATION_PIPELINE_KEY,
    GC_GRR_KEY,
    GenomicContext,
    GenomicContextProvider,
    SimpleGenomicContext,
)

logger = logging.getLogger(__name__)


class CLIAnnotationContextProvider(GenomicContextProvider):
    """Defines annotation pipeline genomics context provider."""

    def __init__(
            self,
    ) -> None:
        """Initialize the CLI pipeline genomic context provider."""
        super().__init__(
            "cli_pipeline_context_provider",
            800,
        )

    @staticmethod
    def add_argparser_arguments(
        parser: argparse.ArgumentParser,
    ) -> None:
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

    def init(self, **kwargs: Any) -> GenomicContext | None:
        """Build a CLI genomic context."""
        # pylint: disable=import-outside-toplevel
        from dae.genomic_resources.genomic_context import (
            get_genomic_context,
        )
        context_objects = {}

        if kwargs.get("pipeline") is None \
                or kwargs["pipeline"] == "context":
            return None
        logger.info(
            "Using the annotation pipeline from the file %s.",
            kwargs["pipeline"])
        grr = get_genomic_context().get_context_object(GC_GRR_KEY)
        assert grr is not None

        pipeline_path = pathlib.Path(kwargs["pipeline"])

        if pipeline_path.exists():
            raw_pipeline = pipeline_path.read_text()
        else:
            pipeline_resource = grr.get_resource(kwargs["pipeline"])
            if pipeline_resource is not None:
                if pipeline_resource.get_type() != "annotation_pipeline":
                    raise TypeError(
                        "Expected an annotation_pipeline resource.")
                raw_pipeline = pipeline_resource.get_file_content(
                    pipeline_resource.get_config()["filename"])
            else:
                raise ValueError(
                    f"The provided argument for an annotation"
                    f" pipeline ('{kwargs['pipeline']}') is neither a valid"
                    f" filepath, nor a valid GRR resource ID.")

        work_dir = None
        if kwargs.get("work_dir"):
            work_dir = pathlib.Path(kwargs["work_dir"])

        pipeline = load_pipeline_from_yaml(
            raw_pipeline, grr,
            allow_repeated_attributes=bool(kwargs.get(
                "allow_repeated_attributes")),
            work_dir=work_dir)
        context_objects[GC_ANNOTATION_PIPELINE_KEY] = pipeline
        return SimpleGenomicContext(
            context_objects, source=("annotation_pipeline_cli",))


def get_context_pipeline(
    context: GenomicContext,
) -> AnnotationPipeline | None:
    """Construct an annotation pipeline."""
    pipeline = context.get_context_object(GC_ANNOTATION_PIPELINE_KEY)
    if pipeline is None:
        return None
    if not isinstance(pipeline, AnnotationPipeline):
        raise TypeError(
            f"The annotation pipeline from the genomic "
            f" context is not an AnnotationPipeline: {type(pipeline)}")
    return pipeline
