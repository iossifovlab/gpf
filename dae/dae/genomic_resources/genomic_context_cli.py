import argparse
import logging
from typing import Any

from dae.genomic_resources.gene_models.gene_models import (
    build_gene_models_from_resource,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)

from .genomic_context_base import (
    GenomicContext,
    GenomicContextProvider,
    SimpleGenomicContext,
)

logger = logging.getLogger(__name__)
GC_GRR_KEY = "genomic_resources_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"


class CLIGenomicContextProvider(GenomicContextProvider):
    """Genomic context provider for CLI."""

    def __init__(
            self,
    ) -> None:
        """Initialize the CLI genomic context provider."""
        super().__init__(
            "cli_genomic_context_provider",
            100,
        )

    @staticmethod
    def add_argparser_arguments(
        parser: argparse.ArgumentParser,
    ) -> None:
        """Add command line arguments to the argument parser."""
        parser.add_argument(
            "-g", "--grr-filename", "--grr", default=None,
            help="The GRR configuration file. If the argument is absent, "
            "the a GRR repository from the current genomic context "
            "(i.e. gpf_instance) will be used or, if that fails, the "
            "default GRR configuration will be used.")
        parser.add_argument(
            "--grr-directory", default=None,
            help="Local GRR directory to use as repository.")
        parser.add_argument(
            "-R", "--reference-genome-resource-id", "--ref", default=None,
            help="The resource id for the reference genome. If the argument "
                 "is absent the reference genome from the current genomic "
                 "context will be used.")
        parser.add_argument(
            "-G", "--gene-models-resource-id", "--genes", default=None,
            help="The resource is of the gene models resource. If the argument"
                 " is absent the gene models from the current genomic "
                 "context will be used.")

    @staticmethod
    def init(**kwargs: Any) -> GenomicContext | None:
        # pylint: disable=import-outside-toplevel
        from .genomic_context import (
            get_genomic_context,
        )

        context_objects: dict[str, Any] = {}
        grr = None
        if kwargs.get("grr_filename") is None \
                and kwargs.get("grr_directory") is None:
            grr = get_genomic_context().get_context_object(GC_GRR_KEY)
        elif kwargs.get("grr_filename") is not None:
            logger.info(
                "Using the GRR configured in the file "
                "%s as requested on the "
                "command line.", kwargs["grr_filename"])
            grr = build_genomic_resource_repository(
                file_name=kwargs["grr_filename"])
        elif kwargs.get("grr_directory") is not None:
            logger.info(
                "Using local GRR directory "
                "%s as requested on the "
                "command line.", kwargs["grr_directory"])
            grr = build_genomic_resource_repository({
                "id": "local",
                "type": "directory",
                "directory": kwargs["grr_directory"],
            })

        if grr is None:
            logger.info(
                "no grr provided in the genomic context; unable to "
                "resolve CLI genomic context")
            return None

        context_objects[GC_GRR_KEY] = grr
        if kwargs.get("reference_genome_resource_id") is not None:
            logger.info(
                "Using the reference genome from resource "
                "%s provided on the command line.",
                kwargs["reference_genome_resource_id"])
            resource = grr.get_resource(kwargs["reference_genome_resource_id"])

            genome = build_reference_genome_from_resource(resource)
            genome.open()
            context_objects[GC_REFERENCE_GENOME_KEY] = genome

        if kwargs.get("gene_models_resource_id") is not None:
            logger.info(
                "Using the gene models from resource "
                "%s provided on the command line.",
                kwargs["gene_models_resource_id"])
            resource = grr.get_resource(kwargs["gene_models_resource_id"])

            gene_models = build_gene_models_from_resource(resource).load()
            context_objects[GC_GENE_MODELS_KEY] = gene_models

        return SimpleGenomicContext(
            context_objects, source=("CLIGenomicContext", ))
