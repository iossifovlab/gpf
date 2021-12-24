from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.repository import GenomicResourceRepo

_REGISTERED_CONEXT_GENERATORS = []

GC_GRR_KEY = "genomic_resource_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"


class GenomicContext(ABC):
    def get_reference_genome(self) -> Optional[ReferenceGenome]:
        o = self.get_context_object(GC_REFERENCE_GENOME_KEY)
        if o is None:
            return None
        if isinstance(o, ReferenceGenome):
            return o
        raise Exception(
            "The conext returned a worng type for a reference genome.")

    def get_gene_models(self) -> Optional[GeneModels]:
        o = self.get_context_object(GC_GENE_MODELS_KEY)
        if o is None:
            return None
        if isinstance(o, GeneModels):
            return o
        raise Exception("The conext returned a wrong type for gene models.")

    def get_genomic_resource_repository(self) -> Optional[GenomicResourceRepo]:
        o = self.get_context_object(GC_GRR_KEY)
        if o is None:
            return None
        if isinstance(o, GenomicResourceRepo):
            return o
        raise Exception("The conext returned a wrong type for "
                        "a genomic resource repository.")

    @abstractmethod
    def get_context_object(self, key) -> Optional[Any]:
        pass


class GenomicContextGenerator(ABC):

    def get_context_generator_priority(self) -> int:
        return 0

    @abstractmethod
    def get_context_generator_type() -> str:
        pass

    @abstractmethod
    def get_contexts() -> List[GenomicContext]:
        pass
    pass


def register_context_source(context_generator: GenomicContextGenerator):
    _REGISTERED_CONEXT_GENERATORS.append(context_generator)


class PriorityGenomicContext(GenomicContext):
    def __init__(self, contexts):
        self.contexts = contexts

    def get_context_object(self, key) -> Optional[Any]:
        for context in self.contexts:
            o = context.get_context_object(key)
            if o:
                return o
        return None


def get_genomic_context() -> GenomicContext:
    contexts = []
    for generator in sorted(_REGISTERED_CONEXT_GENERATORS,
                            key=lambda g: (g.get_context_generator_priority(),
                                           g.get_context_generator_type())):
        contexts += generator.get_contexts()
    return PriorityGenomicContext(contexts)
