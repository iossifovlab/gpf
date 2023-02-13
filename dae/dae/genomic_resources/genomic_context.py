from __future__ import annotations

import argparse
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple, Set, Callable, Dict
from functools import lru_cache

from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from dae.genomic_resources.reference_genome import ReferenceGenome, \
    build_reference_genome_from_resource
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_resource
from dae.genomic_resources.repository import GenomicResourceRepo

_REGISTERED_CONTEXT_PROVIDERS: list[GenomicContextProvider] = []
_REGISTERED_CONTEXTS: list[GenomicContext] = []

GC_GRR_KEY = "genomic_resources_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"

logger = logging.getLogger(__name__)


class GenomicContext(ABC):
    """Abstract base class for genomic context."""

    def get_reference_genome(self) -> Optional[ReferenceGenome]:
        """Return reference genome from context."""
        obj = self.get_context_object(GC_REFERENCE_GENOME_KEY)
        if obj is None:
            return None
        if isinstance(obj, ReferenceGenome):
            return obj
        raise ValueError(
            f"The context returned a wrong type for a reference genome: "
            f"{type(obj)}")

    def get_gene_models(self) -> Optional[GeneModels]:
        """Return gene models from context."""
        obj = self.get_context_object(GC_GENE_MODELS_KEY)
        if obj is None:
            return None
        if isinstance(obj, GeneModels):
            return obj
        raise ValueError(
            f"The context returned a wrong type for gene models: "
            f"{type(obj)}")

    def get_genomic_resources_repository(
            self) -> Optional[GenomicResourceRepo]:
        """Return genomic resources repository from context."""
        obj = self.get_context_object(GC_GRR_KEY)
        if obj is None:
            return None
        if isinstance(obj, GenomicResourceRepo):
            return obj
        raise ValueError(
            f"The context returned a wrong type for GRR: "
            f"{type(obj)}")

    @abstractmethod
    def get_context_object(self, key) -> Optional[Any]:
        """Return a genomic context object corresponding to the passed key.

        If there is no such object returns None.
        """

    @abstractmethod
    def get_context_keys(self) -> Set[str]:
        """Return set of all keys that could be found in the context."""

    @abstractmethod
    def get_source(self) -> Tuple[str, ...]:
        """Return a tuple of strings that identifies the genomic context."""


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

    def get_all_context_objects(self) -> Dict[str, Any]:
        return self._context


class SimpleGenomicContextProvider(GenomicContextProvider):
    """Simple implementation of genomic contexts provider."""

    def __init__(
            self,
            context_builder: Callable[[], GenomicContext],
            provider_type: str,
            priority: int):
        self._type: str = provider_type
        self._priority: int = priority
        self._context_builder = context_builder
        self._contexts: Optional[List[GenomicContext]] = None

    def get_context_provider_priority(self) -> int:
        return self._priority

    def get_context_provider_type(self) -> str:
        return f"SingleGenomicContextProvider[{self._type}]"

    def get_contexts(self) -> List[GenomicContext]:
        if self._contexts is None:
            try:
                context = self._context_builder()
                if context is None:
                    self._contexts = []
                else:
                    self._contexts = [context]
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "problem while building genomic context",
                    exc_info=True)
                self._contexts = []

        return self._contexts


def register_context_provider(context_provider: GenomicContextProvider):
    logger.debug(
        "Registering the %s "
        "genomic context generator with priority %s",
        context_provider.get_context_provider_type(),
        context_provider.get_context_provider_priority())
    _REGISTERED_CONTEXT_PROVIDERS.append(context_provider)


def register_context(context: GenomicContext):
    logger.debug(
        "Registering the %s "
        "genomic context",
        context.get_source())
    _REGISTERED_CONTEXTS.insert(0, context)


class PriorityGenomicContext(GenomicContext):
    """Defines a priority genomic context."""

    def __init__(self, contexts):
        self.contexts = contexts
        if self.contexts:
            logger.info("Using the following genomic context:")
            for context in self.contexts:
                logger.info("\t%s", context.get_source())
        else:
            logger.info("No genomic contexts are available.")

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

    @lru_cache(maxsize=32)
    def get_source(self) -> Tuple[str, ...]:
        result = ["PriorityGenomicContext"]
        for context in self.contexts:
            result.append(str(context.get_source()))
        return tuple(result)


def get_genomic_context() -> GenomicContext:
    contexts = _REGISTERED_CONTEXTS[:]
    for provider in sorted(_REGISTERED_CONTEXT_PROVIDERS,
                           key=lambda g: (g.get_context_provider_priority(),
                                          g.get_context_provider_type())):
        contexts.extend(provider.get_contexts())
    return PriorityGenomicContext(contexts)


class CLIGenomicContext(SimpleGenomicContext):
    """Defines CLI genomics context."""

    @staticmethod
    def add_context_arguments(parser: argparse.ArgumentParser):
        """Add command line arguments to the argument parser."""
        parser.add_argument(
            "-grr", "--grr-filename", default=None,
            help="The GRR configuration file. If the argument is absent, "
            "the a GRR repository from the current genomic context "
            "(i.e. gpf_instance) will be used or, if that fails, the "
            "default GRR configuration will be used.")
        parser.add_argument(
            "--grr-directory", default=None,
            help="Local GRR directory to use as repository.")
        parser.add_argument(
            "-ref", "--reference-genome-resource-id", default=None,
            help="The resource id for the reference genome. If the argument "
                 "is absent the reference genome from the current genomic "
                 "context will be used.")
        parser.add_argument(
            "-genes", "--gene-models-resource-id", default=None,
            help="The resource is of the gene models resource. If the argument"
                 " is absent the gene models from the current genomic "
                 "context will be used.")

    @staticmethod
    def context_builder(args) -> CLIGenomicContext:
        """Build a CLI genomic context."""
        context_objects: Dict[str, Any] = {}
        grr = None
        if args.grr_filename is None and args.grr_directory is None:
            grr = get_genomic_context().get_context_object(GC_GRR_KEY)
        elif args.grr_filename is not None:
            logger.info(
                "Using the GRR configured in the file "
                "%s as requested on the "
                "command line.", args.grr_filename)
            grr = build_genomic_resource_repository(
                file_name=args.grr_filename)
        elif args.grr_directory is not None:
            logger.info(
                "Using local GRR directory "
                "%s as requested on the "
                "command line.", args.grr_directory)
            grr = build_genomic_resource_repository({
                "id": "local",
                "type": "directory",
                "directory": args.grr_directory
            })

        if grr is None:
            raise ValueError("Can't resolve genomic context GRR")

        context_objects[GC_GRR_KEY] = grr
        if args.reference_genome_resource_id is not None:
            logger.info(
                "Using the reference genome from resource "
                "%s provided on the command line.",
                args.reference_genome_resource_id)
            resource = grr.get_resource(args.reference_genome_resource_id)

            genome = build_reference_genome_from_resource(resource)
            genome.open()
            context_objects[GC_REFERENCE_GENOME_KEY] = genome

        if args.gene_models_resource_id is not None:
            logger.info(
                "Using the gene models from resource "
                "%s provided on the command line.",
                args.gene_models_resource_id)
            resource = grr.get_resource(args.gene_models_resource_id)

            gene_models = build_gene_models_from_resource(resource).load()
            context_objects[GC_GENE_MODELS_KEY] = gene_models

        return CLIGenomicContext(
            context_objects, source=("CLIGenomicContext", ))


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
            "DefaultGRRProvider",
            1000)

    @staticmethod
    def register():
        register_context_provider(DefaultRepositoryContextProvider())
