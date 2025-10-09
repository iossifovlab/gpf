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
from typing import Any

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)

from .genomic_context_base import (
    GenomicContext,
    GenomicContextProvider,
    PriorityGenomicContext,
    SimpleGenomicContext,
)

logger = logging.getLogger(__name__)


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

    def init(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> GenomicContext:
        grr = build_genomic_resource_repository()

        return SimpleGenomicContext(
            {
                "genomic_resources_repository": grr,
            },
            ("default_genomic_resources_repository", grr.repo_id),
        )


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
    if _REGISTERED_CONTEXTS:
        logger.debug(
            "Genomic context providers already initialized, skipping.")
        return

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


def clear_registered_contexts() -> None:
    """Clear all registered genomic contexts."""
    _REGISTERED_CONTEXTS.clear()


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


def _load_genomic_context_provider_plugins() -> None:
    # pylint: disable=import-outside-toplevel
    from importlib.metadata import entry_points

    discovered_plugins = entry_points(group="dae.genomic_resources.plugins")
    for plugin in discovered_plugins:
        factory = plugin.load()
        provider = factory()
        assert isinstance(provider, GenomicContextProvider)
        register_context_provider(provider)


_load_genomic_context_provider_plugins()
