import logging
from typing import List, Optional, Any, Tuple, Set

from dae.genomic_resources.genomic_context import GC_GRR_KEY
from dae.genomic_resources.genomic_context import GC_REFERENCE_GENOME_KEY
from dae.genomic_resources.genomic_context import GC_GENE_MODELS_KEY
from dae.genomic_resources.genomic_context import GenomicContext
from dae.genomic_resources.genomic_context import GenomicContextProvider
from dae.genomic_resources.genomic_context import register_context_provider

logger = logging.getLogger(__name__)


class GPFInstanceGenomicContextProvider(GenomicContextProvider):
    """Defines GPFInstance genomic context provider."""

    def __init__(self):
        self.contexts: Optional[List[GenomicContext]] = None

    def get_context_generator_priority(self) -> int:
        return 100

    def get_context_generator_type(self) -> str:
        return "gpf_instance"

    def get_contexts(self) -> List[GenomicContext]:
        if self.contexts is None:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance

            class GPFInstanceGenomicContext(GenomicContext):
                """Defines GPFInstance genomic context."""

                def __init__(self, gpf_instance: GPFInstance):
                    self.gpf_instance: GPFInstance = gpf_instance

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
                    return ("gpf_instance", self.gpf_instance.dae_db_dir)

            self.contexts = []
            try:
                self.contexts.append(GPFInstanceGenomicContext(GPFInstance()))
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "problem while initializing default gpf instance",
                    exc_info=True)

        return self.contexts


def init_gpf_instance_genomic_context_plugin():
    register_context_provider(GPFInstanceGenomicContextProvider())
