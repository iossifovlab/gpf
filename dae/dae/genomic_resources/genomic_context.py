from __future__ import annotations

import argparse
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple, Set, Callable, Dict
from functools import cache

from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from dae.genomic_resources.reference_genome import ReferenceGenome, \
    build_reference_genome_from_resource
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_resource
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

    @abstractmethod
    def get_context_provider_priority(self) -> int:
        # pylint: disable=no-self-use
        pass

    @abstractmethod
    def get_context_provider_type(self) -> str:
        pass

    @abstractmethod
    def get_contexts(self) -> List[GenomicContext]:
        pass


class SimpleGenomicContext(GenomicContext):
    """Simple implementation of genomic context."""

    def __init__(
            self, context_objects: Dict[str, Any], source: Tuple[str, ...]):
        self._context: Dict[str, Any] = context_objects
        self._source = source

    def get_context_object(self, key) -> Optional[Any]:
        return self._context.get(key)

    def get_context_keys(self):
        return set(self._context.keys())

    def get_source(self) -> Tuple[str, ...]:
        return self._source


class SimpleGenomicContextProvider(GenomicContextProvider):
    """Simple implementation of genomic contexts provider."""

    def __init__(
            self,
            context_builder: Callable[[], GenomicContext],
            priority: int):
        self._priority: int = priority
        self._context_builder = context_builder
        self._contexts: Optional[List[GenomicContext]] = None

    def get_context_provider_priority(self) -> int:
        return self._priority

    def get_context_provider_type(self) -> str:
        if self._contexts is None:
            sources: List[Tuple[str, ...]] = [("not initialized", )]
        else:
            sources = [c.get_source() for c in self._contexts]
        return f"SingleGenomicContextProvider{sources}"

    def get_contexts(self) -> List[GenomicContext]:
        if self._contexts is None:
            try:
                self._contexts = [self._context_builder()]
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "problem while building genomic context",
                    exc_info=True)
                self._contexts = []

        return self._contexts


def register_context_provider(context_provider: GenomicContextProvider):
    logger.debug(
        "Registerfing the %s "
        "genomic context generator with priority %s",
        context_provider.get_context_provider_type(),
        context_provider.get_context_provider_type())
    _REGISTERED_CONEXT_PROVIDERS.append(context_provider)


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
                           key=lambda g: (g.get_context_provider_priority(),
                                          g.get_context_provider_type())):
        contexts.extend(provider.get_contexts())
    return PriorityGenomicContext(contexts)


class CLIGenomicContext(GenomicContext):
    """Defines CLI genomics context."""

    def __init__(self, grr, genome, gene_models):
        self._grr: GenomicResourceRepo = grr
        self._ref_genome: Optional[ReferenceGenome] = genome
        self._gene_models: Optional[GeneModels] = gene_models

    def get_context_object(self, key) -> Optional[Any]:
        if key == GC_GRR_KEY and self._grr is not None:
            return self._grr
        if key == GC_REFERENCE_GENOME_KEY and self._ref_genome is not None:
            return self._ref_genome
        if key == GC_GENE_MODELS_KEY and self._gene_models is not None:
            return self._gene_models
        logger.info(
            "genomic context object with key %s not found in %s",
            key, self.get_source())
        return None

    @cache
    def get_context_keys(self) -> Set[str]:
        result = set()
        if self._grr is not None:
            result.add(GC_GRR_KEY)
        if self._ref_genome is not None:
            result.add(GC_REFERENCE_GENOME_KEY)
        if self._gene_models is not None:
            result.add(GC_GENE_MODELS_KEY)
        return result

    def get_source(self) -> Tuple[str, ...]:
        return ("CLIGenomicContext",)


class CLIGenomicContextProvider(SimpleGenomicContextProvider):
    """Defines CLI genomic context provider."""

    @staticmethod
    def add_context_arguments(parser: argparse.ArgumentParser):
        """Add command line arguments to the argument parser."""
        parser.add_argument(
            "-grr", "--grr-file-name", default=None,
            help="The GRR configuration file. If the argument is absent, "
            "the a GRR repository from the current genomic context "
            "(i.e. gpf_instance) will be used or, if that fails, the "
            "default GRR configuration will be used.")
        parser.add_argument(
            "-ref", "--reference-genome-resource-id", default=None,
            help="The resource id for the reference genome. If the argument "
                 "is absent the reference genome from the current genomic "
                 "context will be used.")
        parser.add_argument(
            "-genes", "--gene-models-resource-id", default=None,
            help="The resource is of the gene models resoruce. If the argument"
                 " is absent the gene models from the current genomic "
                 "context will be used.")

    @staticmethod
    def context_builder(args) -> CLIGenomicContext:
        """Build a CLI genomic context."""
        grr = None
        if args.grr_filename is None:
            grr = get_genomic_context().get_context_object(GC_GRR_KEY)
        else:
            logger.info(
                "Using the GRR consigured in the file "
                "%s as requested on the "
                "command line.", args.grr_file_name)
            grr = build_genomic_resource_repository(
                file_name=args.grr_file_name)

        if grr is None:
            raise ValueError("Can't resolve genomic context GRR")

        genome: Optional[ReferenceGenome] = None
        if args.reference_genome_resource_id is not None:
            logger.info(
                "Using the reference genome from resoruce "
                "%s provided on the command line.",
                args.reference_genome_resource_id)
            resource = grr.get_resource(args.reference_genome_resource_id)

            genome = build_reference_genome_from_resource(resource)

        gene_models: Optional[GeneModels] = None
        if args.gene_models_resource_id is not None:
            logger.info(
                "Using the gene models from resoruce "
                "%s provided on the command line.",
                args.gene_models_resource_id)
            resource = grr.get_resource(args.gene_models_resource_id)

            gene_models = build_gene_models_from_resource(resource)

        return CLIGenomicContext(grr, genome, gene_models)


class DefaultRepositoryContextProvider(SimpleGenomicContextProvider):
    """Genomic context provider for default GRR."""

    @staticmethod
    def context_builder():
        grr = build_genomic_resource_repository()
        return SimpleGenomicContext(
            {
                GC_GRR_KEY: grr
            },
            ("default_genomic_resources_repository", grr.repo_id)
        )

    def __init__(self):
        super().__init__(
            DefaultRepositoryContextProvider.context_builder,
            1000)

    @staticmethod
    def register():
        register_context_provider(DefaultRepositoryContextProvider())
