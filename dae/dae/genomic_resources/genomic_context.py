"""
Genomic context provides a way to collect various genomic resources from
various sources and make them available through a single interface.

Example usage of genomic context in a tool with command line interface:

.. code-block:: python

    import argparse
    import sys

    from dae.genomic_resources.genomic_context import (
        context_providers_add_argparser_arguments,
        context_providers_init,
        get_genomic_context,
    )


    parser = argparse.ArgumentParser()
    context_providers_add_argparser_arguments(parser)

    args = parser.parse_args(sys.argv[1:])
    context_providers_init(**vars(args))
    genomic_context = get_genomic_context()

If you don't need command line arguments you can do:

.. code-block:: python

    context_providers_init()
    genomic_context = get_genomic_context()

When you need a CLI with all defaults and without modifying the argument
parser you can do:

.. code-block:: python

    context_providers_init_with_argparser(toolname: str)
    genomic_context = get_genomic_context()


"""
from __future__ import annotations

import argparse
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from importlib.metadata import entry_points
from typing import Any

from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)

logger = logging.getLogger(__name__)
GC_GRR_KEY = "genomic_resources_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"
GC_ANNOTATION_PIPELINE_KEY = "annotation_pipeline"
GC_GENOTYPE_STORAGES_KEY = "genotype_storages"
GC_GPF_INSTANCE_KEY = "gpf_instance"


class GenomicContext(ABC):
    """Abstract base class for genomic context."""

    def get_reference_genome(self) -> ReferenceGenome | None:
        """Return reference genome from context."""
        obj = self.get_context_object(GC_REFERENCE_GENOME_KEY)
        if obj is None:
            return None
        if isinstance(obj, ReferenceGenome):
            return obj
        raise ValueError(
            f"The context returned a wrong type for a reference genome: "
            f"{type(obj)}")

    def get_gene_models(self) -> GeneModels | None:
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
            self) -> GenomicResourceRepo | None:
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
    def get_context_object(self, key: str) -> Any | None:
        """Return a genomic context object corresponding to the passed key.

        If there is no such object returns None.
        """

    @abstractmethod
    def get_context_keys(self) -> set[str]:
        """Return set of all keys that could be found in the context."""

    @abstractmethod
    def get_source(self) -> tuple[str, ...]:
        """Return a tuple of strings that identifies the genomic context."""


class GenomicContextProvider:
    """Abstract base class for genomic contexts provider."""

    def __init__(self, provider_type: str, provider_priority: int) -> None:
        """Initialize the genomic context provider."""
        self._provider_type = provider_type
        self._provider_priority = provider_priority

    def get_context_provider_priority(self) -> int:
        return self._provider_priority

    def get_context_provider_type(self) -> str:
        return self._provider_type

    @staticmethod
    def add_argparser_arguments(
        parser: argparse.ArgumentParser,
    ) -> None:
        """Add command line arguments to the argument parser."""
        raise NotImplementedError

    @staticmethod
    def init(**kwargs: Any) -> GenomicContext | None:
        """Build the genomic context based on the provided arguments."""
        raise NotImplementedError


class SimpleGenomicContext(GenomicContext):
    """Simple implementation of genomic context."""

    def __init__(
        self, context_objects: dict[str, Any],
        source: tuple[str, ...],
    ):
        self._context: dict[str, Any] = context_objects
        self._source = source

    def get_context_object(self, key: str) -> Any | None:
        return self._context.get(key)

    def get_context_keys(self) -> set[str]:
        return set(self._context.keys())

    def get_source(self) -> tuple[str, ...]:
        return self._source

    def get_all_context_objects(self) -> dict[str, Any]:
        return self._context


class PriorityGenomicContext(GenomicContext):
    """Defines a priority genomic context."""

    def __init__(self, contexts: Iterable[GenomicContext]):
        self.contexts = contexts
        if self.contexts:
            logger.info("Using the following genomic context:")
            for context in self.contexts:
                logger.info("\t%s", context.get_source())
        else:
            logger.info("No genomic contexts are available.")

    def get_context_object(self, key: str) -> Any | None:
        for context in self.contexts:
            obj = context.get_context_object(key)
            if obj:
                logger.info(
                    "object with key %s found in the context %s",
                    key, context.get_source())
                return obj
        return None

    def get_context_keys(self) -> set[str]:
        result: set[str] = set()
        for context in self.contexts:
            result = result.union(context.get_context_keys())
        return result

    def get_source(self) -> tuple[str, ...]:
        result = ["PriorityGenomicContext"]
        result.extend([str(context.get_source()) for context in self.contexts])
        return tuple(result)


class DefaultRepositoryContextProvider(GenomicContextProvider):
    """Genomic context provider for default GRR."""

    def __init__(self) -> None:
        super().__init__(
            "DefaultGRRProvider",
            10_000)

    @staticmethod
    def add_argparser_arguments(
        parser: argparse.ArgumentParser,
    ) -> None:
        # No arguments needed for default GRR context provider
        pass

    @staticmethod
    def init(
        **kwargs: Any,  # noqa: ARG004
    ) -> GenomicContext:
        grr = build_genomic_resource_repository()

        return SimpleGenomicContext(
            {
                "genomic_resources_repository": grr,
            },
            ("default_genomic_resources_repository", grr.repo_id),
        )


_CONTEXT_PLUGINS_LOADED = False
_REGISTERED_CONTEXT_PROVIDERS: list[GenomicContextProvider] = []
_REGISTERED_CONTEXTS: list[GenomicContext] = []


def register_context_provider(
    context_provider: GenomicContextProvider,
) -> None:
    """Register genomic context provider."""
    logger.debug(
        "Registering the %s "
        "genomic context generator with priority %s",
        context_provider.get_context_provider_type(),
        context_provider.get_context_provider_priority())
    _REGISTERED_CONTEXT_PROVIDERS.append(context_provider)


def context_providers_init(**kwargs: Any) -> None:
    """Initialize all registered genomic context providers."""
    for provider in sorted(
            _REGISTERED_CONTEXT_PROVIDERS,
            key=lambda g: (- g.get_context_provider_priority(),
                           g.get_context_provider_type())):

        context = provider.init(**kwargs)
        if context is None:
            logger.info(
                "genomic context provider %s unable to create a context",
                provider.get_context_provider_type(),
            )
            continue
        register_context(context)


def context_providers_add_argparser_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """Add command line arguments for all registered context providers."""
    for provider in sorted(
            _REGISTERED_CONTEXT_PROVIDERS,
            key=lambda g: (- g.get_context_provider_priority(),
                           g.get_context_provider_type())):
        provider.add_argparser_arguments(parser)


def register_context(context: GenomicContext) -> None:
    logger.debug(
        "registering the %s "
        "genomic context",
        context.get_source())
    _REGISTERED_CONTEXTS.insert(0, context)


def get_genomic_context() -> GenomicContext:
    """Collect all registered context and returns a priority context."""
    contexts = _REGISTERED_CONTEXTS[:]
    return PriorityGenomicContext(contexts)


def _load_context_provider_plugins() -> None:
    # pylint: disable=global-statement
    global _CONTEXT_PLUGINS_LOADED

    if _CONTEXT_PLUGINS_LOADED:
        return

    discovered_plugins = entry_points(group="dae.genomic_resources.plugins")
    for plugin in discovered_plugins:
        factory = plugin.load()
        provider = factory()
        assert isinstance(provider, GenomicContextProvider)
        register_context_provider(provider)
    _CONTEXT_PLUGINS_LOADED = True


_load_context_provider_plugins()
