"""
Genomic context provides a way to collect various genomic resources from
various sources and make them available through a single interface.

The module follows a registry-based approach.  Providers register themselves
and are later consulted (in priority order) to build individual
:class:`~dae.genomic_resources.genomic_context_base.GenomicContext`
instances.  Every created context is combined into a
:class:`PriorityGenomicContext`, offering a single access point for
resources such as genomic resource repositories, reference genomes,
gene models, annotation pipelines, etc. Providers can be registered
programmatically via :func:`register_context_provider` or discovered
automatically through entry points.

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

    context_providers_init_with_argparser("GenomicTool")
    genomic_context = get_genomic_context()


"""
from __future__ import annotations

import argparse
import logging
import sys
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
    """Provide access to the default genomic resources repository.

    The default repository is resolved via
    :func:`build_genomic_resource_repository` using the environment
    configuration.  The resulting context exposes a single key,
    ``"genomic_resources_repository"``, which can be consumed by other code
    participating in the context chain.
    """

    def __init__(self) -> None:
        super().__init__(
            "DefaultGRRProvider",
            10_000)

    def add_argparser_arguments(
        self, parser: argparse.ArgumentParser,
        **kwargs: Any,
    ) -> None:
        """Declare command line arguments for this provider.

        The default repository provider is fully configuration driven and has
        nothing to expose on the CLI, so the method intentionally leaves the
        *parser* untouched.  The override exists to make the behaviour explicit
        in the generated documentation.
        """

    def init(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> GenomicContext:
        """Instantiate a context backed by the default GRR.

        Parameters
        ----------
        **kwargs
            Accepted for interface compatibility; the provider ignores runtime
            keyword arguments because everything is derived from the global
            configuration.

        Returns
        -------
        GenomicContext
            A context exposing a single ``genomic_resources_repository`` entry
            pointing at the default repository instance.
        """
        grr = build_genomic_resource_repository()

        return SimpleGenomicContext(
            {
                "genomic_resources_repository": grr,
            },
            source=f"DefaultRepositoryContextProvider({grr.repo_id})",
        )


_REGISTERED_CONTEXT_PROVIDERS: list[GenomicContextProvider] = []
"""Collection of provider instances awaiting initialisation."""
_REGISTERED_CONTEXTS: list[GenomicContext] = []
"""Contexts produced during :func:`context_providers_init`."""


def register_context_provider(
    context_provider: GenomicContextProvider,
) -> None:
    """Register *context_provider* so it participates in initialization.

    Parameters
    ----------
    context_provider
        The provider implementation that should be considered when contexts
        are assembled.  Providers are stored in registration order and later
        sorted by their priority before initialization.
    """
    logger.debug(
        "Registering the %s "
        "genomic context generator with priority %s",
        context_provider.get_context_provider_type(),
        context_provider.get_context_provider_priority())
    _REGISTERED_CONTEXT_PROVIDERS.append(context_provider)


def context_providers_init(**kwargs: Any) -> None:
    """Materialize contexts from every registered provider.

    The function walks all registered providers in priority order and asks
    each of them to initialise a :class:`GenomicContext`.  The resulting
    contexts are stored for later retrieval via :func:`get_genomic_context`.

    Notes
    -----
    Providers are invoked at most once per process.  Subsequent calls are
    ignored until :func:`clear_registered_contexts` is executed, which is
    especially helpful in unit tests.

    Parameters
    ----------
    **kwargs
        Keyword arguments forwarded to every provider's ``init`` method.
    """
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


def context_providers_init_with_argparser(
    toolname: str = "GenomicTool",
) -> None:
    """Initialise providers using arguments parsed from ``sys.argv``.

    Parameters
    ----------
    toolname
        The program name presented to :class:`argparse.ArgumentParser`.

    Notes
    -----
    This helper is useful for simple tools that do not customise their
    argument parser but still want to expose the command line options defined
    by registered context providers.
    """
    parser = argparse.ArgumentParser(prog=toolname)
    context_providers_add_argparser_arguments(parser)
    args = parser.parse_args(sys.argv[1:])
    context_providers_init(**vars(args))


def clear_registered_contexts() -> None:
    """Forget all contexts created by :func:`context_providers_init`.

    This function exists primarily for testing scenarios where the global
    registry should be reset between test cases.
    """
    _REGISTERED_CONTEXTS.clear()


def context_providers_add_argparser_arguments(
    parser: argparse.ArgumentParser,
    **kwargs: Any,
) -> None:
    """Delegate command line argument registration to each provider.

    Parameters
    ----------
    parser
        The parser that should receive additional arguments from every
        registered provider.
    """
    for provider in sorted(
            _REGISTERED_CONTEXT_PROVIDERS,
            key=lambda g: (- g.get_context_provider_priority(),
                           g.get_context_provider_type())):
        provider.add_argparser_arguments(parser, **kwargs)


def register_context(context: GenomicContext) -> None:
    """Record *context* so it participates in future lookups.

    Parameters
    ----------
    context
        The context instance to be considered when
        :func:`get_genomic_context` is invoked.
    """
    logger.debug(
        "registering the %s "
        "genomic context",
        context.get_source())
    _REGISTERED_CONTEXTS.insert(0, context)


def get_genomic_context() -> GenomicContext:
    """Return a priority context that merges every registered context.

    The returned :class:`PriorityGenomicContext` respects the registration
    order, giving precedence to contexts added most recently when multiple
    contexts expose the same key.
    """
    contexts = _REGISTERED_CONTEXTS[:]
    return PriorityGenomicContext(contexts)


def _load_genomic_context_provider_plugins() -> None:
    """Discover context providers published via ``entry_points``.

    The function is executed at import time so the default providers become
    available automatically.  Every entry point is expected to expose a
    callable returning a :class:`GenomicContextProvider` instance.

    Notes
    -----
    Third-party packages can contribute providers by declaring the
    ``dae.genomic_resources.plugins`` entry-point group in their project
    metadata (for example, ``pyproject.toml``).
    """
    # pylint: disable=import-outside-toplevel
    from importlib.metadata import entry_points

    discovered_plugins = entry_points(group="dae.genomic_resources.plugins")
    for plugin in discovered_plugins:
        factory = plugin.load()
        provider = factory()
        assert isinstance(provider, GenomicContextProvider)
        register_context_provider(provider)


_load_genomic_context_provider_plugins()
