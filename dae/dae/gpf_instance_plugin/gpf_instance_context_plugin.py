import argparse
import logging
from typing import Any

from dae.genomic_resources.genomic_context_base import (
    GC_ANNOTATION_PIPELINE_KEY,
    GC_GENE_MODELS_KEY,
    GC_GRR_KEY,
    GC_REFERENCE_GENOME_KEY,
    GenomicContext,
    GenomicContextProvider,
)

logger = logging.getLogger(__name__)
GC_GPF_INSTANCE_KEY = "gpf_instance"
GC_GENOTYPE_STORAGES_KEY = "genotype_storages"


class GPFInstanceGenomicContext(GenomicContext):
    """Defines GPFInstance genomic context."""

    def __init__(self, gpf_instance: Any) -> None:
        # pylint: disable=import-outside-toplevel
        from dae.gpf_instance.gpf_instance import GPFInstance
        if not isinstance(gpf_instance, GPFInstance):
            raise TypeError(
                f"invalid gpf instance type: {type(gpf_instance)}")

        self.gpf_instance = gpf_instance

    def get_context_object(self, key: str) -> Any | None:
        if key == GC_GENE_MODELS_KEY:
            return self.gpf_instance.gene_models
        if key == GC_REFERENCE_GENOME_KEY:
            return self.gpf_instance.reference_genome
        if key == GC_GRR_KEY:
            return self.gpf_instance.grr
        if key == GC_ANNOTATION_PIPELINE_KEY:
            return self.gpf_instance.get_annotation_pipeline()
        if key == GC_GENOTYPE_STORAGES_KEY:
            return self.gpf_instance.genotype_storages
        if key == GC_GPF_INSTANCE_KEY:
            return self.gpf_instance
        logger.info(
            "can't find %s in GPF instance genomic context", key)
        return None

    def get_context_keys(self) -> set[str]:
        return {
            GC_GENE_MODELS_KEY, GC_REFERENCE_GENOME_KEY,
            GC_GRR_KEY, GC_GENOTYPE_STORAGES_KEY, GC_ANNOTATION_PIPELINE_KEY,
            GC_GPF_INSTANCE_KEY,
        }

    def get_source(self) -> str:
        return f"GPFInstanceGenomicContext({self.gpf_instance.dae_dir})"


class GPFInstanceContextProvider(GenomicContextProvider):
    """Defines GPFInstance genomic context provider."""

    def __init__(self) -> None:
        super().__init__(
            "GPFInstanceProvider",
            2000)

    def add_argparser_arguments(
        self, parser: argparse.ArgumentParser,
    ) -> None:
        """Add command line arguments to the argument parser."""
        parser.add_argument(
            "-i", "--instance", "--gpf-instance", default=None,
            help="The path to the GPF instance configuration file.")

    def init(self, **kwargs: Any) -> GenomicContext | None:
        """Initialize the GPF instance genomic context."""
        # pylint: disable=import-outside-toplevel
        from dae.gpf_instance.gpf_instance import GPFInstance
        gpf_instance = kwargs.get("gpf_instance")
        if gpf_instance is not None:
            if not isinstance(gpf_instance, GPFInstance):
                raise TypeError(
                    f"Invalid type for gpf_instance: {type(gpf_instance)}")
            return GPFInstanceGenomicContext(gpf_instance)

        try:
            gpf_instance = GPFInstance.build(
                config_filename=kwargs.get("instance"))
        except ValueError:
            return None

        return GPFInstanceGenomicContext(gpf_instance)
