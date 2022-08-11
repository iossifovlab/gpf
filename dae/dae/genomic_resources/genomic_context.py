from functools import cache
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple, Set
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.repository import GenomicResourceRepo

_REGISTERED_CONEXT_PROVIDERS: list = []

GC_GRR_KEY = "genomic_resource_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"

logger = logging.getLogger(__name__)


class GenomicContext(ABC):
    """Abstract base class for genomic context."""

    def get_reference_genome(self) -> Optional[ReferenceGenome]:
        obj = self.get_context_object(GC_REFERENCE_GENOME_KEY)
        if obj is None:
            return None
        if isinstance(obj, ReferenceGenome):
            return obj
        raise ValueError(
            "The conext returned a worng type for a reference genome.")

    def get_gene_models(self) -> Optional[GeneModels]:
        obj = self.get_context_object(GC_GENE_MODELS_KEY)
        if obj is None:
            return None
        if isinstance(obj, GeneModels):
            return obj
        raise ValueError("The conext returned a wrong type for gene models.")

    def get_genomic_resource_repository(self) -> Optional[GenomicResourceRepo]:
        obj = self.get_context_object(GC_GRR_KEY)
        if obj is None:
            return None
        if isinstance(obj, GenomicResourceRepo):
            return obj
        raise ValueError(
            "The conext returned a wrong type for "
            "a genomic resource repository.")

    @abstractmethod
    def get_context_object(self, key) -> Optional[Any]:
        pass

    @abstractmethod
    def get_context_keys(self) -> Set[str]:
        pass

    @abstractmethod
    def get_source(self) -> Tuple[str, ...]:
        pass


class GenomicContextProvider(ABC):
    """Abstract base class for genomic contexts provider."""

    def get_context_generator_priority(self) -> int:
        # pylint: disable=no-self-use
        return 0

    @abstractmethod
    def get_context_generator_type(self) -> str:
        pass

    @abstractmethod
    def get_contexts(self) -> List[GenomicContext]:
        pass


def register_context_provider(context_generator: GenomicContextProvider):
    logger.debug(
        "Registerfing the %s "
        "genomic context generator with priority %s",
        context_generator.get_context_generator_type(),
        context_generator.get_context_generator_type())
    _REGISTERED_CONEXT_PROVIDERS.append(context_generator)


class PriorityGenomicContext(GenomicContext):
    """Defines a priority genomic context."""

    def __init__(self, contexts):
        self.contexts = contexts
        if self.contexts:
            logger.info("Using the folloing genomic context:")
            for context in self.contexts:
                logger.info("\t%s", context.get_source())
        else:
            logger.info("No genomic context are available.")

    def get_context_object(self, key) -> Optional[Any]:
        for context in self.contexts:
            obj = context.get_context_object(key)
            if obj:
                logger.info(
                    "object with key %s found in the context %s",
                    key, context.get_source())
                return obj
        return None

    def get_context_keys(self) -> Set[str]:
        result: Set[str] = set()
        for context in self.contexts:
            result = result.union(context.get_context_keys())
        return result

    @cache
    def get_source(self) -> Tuple[str, ...]:
        result = ["PriorityGenomicContext"]
        for context in self.contexts:
            result.append(context.get_source())
        return tuple(result)


def get_genomic_context() -> GenomicContext:
    contexts = []
    for provider in sorted(_REGISTERED_CONEXT_PROVIDERS,
                           key=lambda g: (g.get_context_generator_priority(),
                                          g.get_context_generator_type())):
        contexts += provider.get_contexts()
    return PriorityGenomicContext(contexts)
