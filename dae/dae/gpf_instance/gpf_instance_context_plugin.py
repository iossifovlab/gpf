from typing import List, Optional, Any

from dae.genomic_resources.genomic_context import GC_GRR_KEY
from dae.genomic_resources.genomic_context import GC_REFERENCE_GENOME_KEY
from dae.genomic_resources.genomic_context import GC_GENE_MODELS_KEY
from dae.genomic_resources.genomic_context import GenomicContext
from dae.genomic_resources.genomic_context import GenomicContextGenerator
from dae.genomic_resources.genomic_context import register_context_source
from dae.gpf_instance.gpf_instance import GPFInstance


class GPFInstanceGenomicContext(GenomicContext):
    def __init__(self, gpf_instance: GPFInstance):
        self.gpf_instance: GPFInstance = gpf_instance

    def get_context_object(self, key) -> Optional[Any]:
        if key == GC_GENE_MODELS_KEY:
            return self.gpf_instance.gene_models
        elif key == GC_REFERENCE_GENOME_KEY:
            return self.gpf_instance.reference_genome
        elif key == GC_GRR_KEY:
            return self.gpf_instance.grr
        elif key == "annotation_pipeline":
            return self.gpf_instance.get_annotation_pipeline()
        elif key == "gpf_instance":
            return self.gpf_instance
        else:
            return None


class GPFInstanceGenomicContextGenerator(GenomicContextGenerator):
    def __init__(self):
        self.contexts = []

        try:
            self.contexts.append(GPFInstanceGenomicContext(GPFInstance()))
        except Exception:
            pass

    def get_context_generator_priority(self) -> int:
        return 100

    def get_context_generator_type(self) -> str:
        return "gpf_instance"

    def get_contexts(self) -> List[GenomicContext]:
        return self.contexts


def init_gpf_instance_genomic_context_plugin():
    register_context_source(GPFInstanceGenomicContextGenerator())
