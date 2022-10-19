import logging
from typing import Optional, Any, Tuple, Set

from dae.genomic_resources.genomic_context import GC_GRR_KEY
from dae.genomic_resources.genomic_context import GC_REFERENCE_GENOME_KEY
from dae.genomic_resources.genomic_context import GC_GENE_MODELS_KEY
from dae.genomic_resources.genomic_context import GenomicContext
from dae.genomic_resources.genomic_context import SimpleGenomicContextProvider
from dae.genomic_resources.genomic_context import register_context_provider

logger = logging.getLogger(__name__)


class GPFInstanceGenomicContext(GenomicContext):
    """Defines GPFInstance genomic context."""

    def __init__(self, gpf_instance):
        self.gpf_instance = gpf_instance

    def get_context_object(self, key) -> Optional[Any]:
        if key == GC_GENE_MODELS_KEY:
            return self.gpf_instance.gene_models
        if key == GC_REFERENCE_GENOME_KEY:
            return self.gpf_instance.reference_genome
        if key == GC_GRR_KEY:
            return self.gpf_instance.grr
        if key == "annotation_pipeline":
            return self.gpf_instance.get_annotation_pipeline()
        if key == "gpf_instance":
            return self.gpf_instance
        logger.info(
            "can't find %s in GPF instance genomic context", key)
        return None

    def get_context_keys(self) -> Set[str]:
        return {
            GC_GENE_MODELS_KEY, GC_REFERENCE_GENOME_KEY,
            GC_GRR_KEY, "annotation_pipeline", "gpf_instance"
        }

    def get_source(self) -> Tuple[str, ...]:
        return ("gpf_instance", self.gpf_instance.dae_dir)


class GPFInstanceGenomicContextProvider(SimpleGenomicContextProvider):
    """Defines GPFInstance genomic context provider."""

    @staticmethod
    def context_builder():
        """Build GPF instance genomic context."""
        try:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance
            return GPFInstanceGenomicContext(GPFInstance.build())
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(
                "unable to create default gpf instance context: %s", ex)
            return None

    def __init__(self):
        super().__init__(
            GPFInstanceGenomicContextProvider.context_builder,
            "GPFInstanceProvider",
            100)


def init_gpf_instance_genomic_context_plugin():
    register_context_provider(GPFInstanceGenomicContextProvider())
