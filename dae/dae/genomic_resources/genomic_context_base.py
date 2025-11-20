"""Base classes and interfaces for genomic context management.

This module defines the foundational abstractions for organizing and
accessing genomic resources through a unified context system.  The central
concept is :class:`GenomicContext`, which acts as a key-value store
exposing resources like genomic repositories, reference genomes, gene
models, and annotation pipelines.  Providers implementing
:class:`GenomicContextProvider` are responsible for building concrete
context instances, often by consulting configuration files or command-line
arguments.

The module also provides two concrete context implementations:
:class:`SimpleGenomicContext` for straightforward dictionary-backed contexts
and :class:`PriorityGenomicContext` for merging multiple contexts with
fallback semantics.

Key Constants
-------------
GC_GRR_KEY : str
    Standard key for the genomic resources repository object.
GC_REFERENCE_GENOME_KEY : str
    Standard key for the reference genome object.
GC_GENE_MODELS_KEY : str
    Standard key for the gene models object.
GC_ANNOTATION_PIPELINE_KEY : str
    Standard key for the annotation pipeline object.

See Also
--------
dae.genomic_resources.genomic_context
    High-level orchestration and provider registration functions.
"""
from __future__ import annotations

import argparse
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from dae.genomic_resources.gene_models import (
    GeneModels,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
)
from dae.genomic_resources.repository import GenomicResourceRepo

logger = logging.getLogger(__name__)
GC_GRR_KEY = "genomic_resources_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"
GC_ANNOTATION_PIPELINE_KEY = "annotation_pipeline"


class GenomicContext(ABC):
    """Abstract base class for genomic context implementations.

    A genomic context serves as a registry of genomic resources, exposing
    them via string keys.  Typical resources include genomic resource
    repositories, reference genomes, gene models, and annotation pipelines.
    Subclasses must implement the key-value retrieval logic and report which
    keys are available.

    Notes
    -----
    The class provides three typed convenience accessors
    (:meth:`get_reference_genome`, :meth:`get_gene_models`,
    :meth:`get_genomic_resources_repository`) that validate the underlying
    object types before returning them.  These accessors raise
    :exc:`ValueError` if the stored object does not match the expected type.
    """

    def get_reference_genome(self) -> ReferenceGenome | None:
        """Retrieve and validate the reference genome from the context.

        Returns
        -------
        ReferenceGenome | None
            The reference genome instance if present and correctly typed, or
            ``None`` when the key is absent.

        Raises
        ------
        ValueError
            If the context entry for :const:`GC_REFERENCE_GENOME_KEY` is
            present but does not contain a :class:`ReferenceGenome` instance.
        """
        obj = self.get_context_object(GC_REFERENCE_GENOME_KEY)
        if obj is None:
            return None
        if isinstance(obj, ReferenceGenome):
            return obj
        raise ValueError(
            f"The context returned a wrong type for a reference genome: "
            f"{type(obj)}")

    def get_gene_models(self) -> GeneModels | None:
        """Retrieve and validate the gene models from the context.

        Returns
        -------
        GeneModels | None
            The gene models instance if present and correctly typed, or
            ``None`` when the key is absent.

        Raises
        ------
        ValueError
            If the context entry for :const:`GC_GENE_MODELS_KEY` is present
            but does not contain a :class:`GeneModels` instance.
        """
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
        """Retrieve and validate the genomic resources repository.

        Returns
        -------
        GenomicResourceRepo | None
            The repository instance if present and correctly typed, or
            ``None`` when the key is absent.

        Raises
        ------
        ValueError
            If the context entry for :const:`GC_GRR_KEY` is present but does
            not contain a :class:`GenomicResourceRepo` instance.
        """
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
        """Retrieve a context object by its key.

        Parameters
        ----------
        key
            The string identifier for the desired resource.

        Returns
        -------
        Any | None
            The stored object if the key is present, otherwise ``None``.

        Notes
        -----
        Implementations must return ``None`` when the key is absent rather
        than raising :exc:`KeyError`.  This convention allows callers to
        safely query for optional resources.
        """

    @abstractmethod
    def get_context_keys(self) -> set[str]:
        """Report all keys exposed by this context.

        Returns
        -------
        set[str]
            The complete collection of keys under which objects can be
            retrieved.  May be empty if the context holds no resources.
        """

    @abstractmethod
    def get_source(self) -> str:
        """Identify the origin of this context.

        Returns
        -------
        str
            A human-readable label describing the source, such as a provider
            name or a file path.  Useful for debugging and logging when
            multiple contexts are combined.
        """


class GenomicContextProvider(ABC):
    """Abstract base class for genomic context providers.

    Providers are responsible for building :class:`GenomicContext` instances
    by consulting external configuration sources, command-line arguments, or
    environment settings.  Each provider is identified by a unique type name
    and assigned a priority that determines the order in which providers are
    invoked during context initialization.

    Providers typically register themselves at module import time by calling
    :func:`dae.genomic_resources.genomic_context.register_context_provider`.
    The registration system later sorts providers by priority (descending) and
    type name, then invokes their :meth:`init` method to produce contexts.

    Attributes
    ----------
    _provider_type : str
        A unique identifier describing this provider.
    _provider_priority : int
        The numeric priority; higher values are consulted first.
    """

    def __init__(self, provider_type: str, provider_priority: int) -> None:
        """Initialize the provider with a type and priority.

        Parameters
        ----------
        provider_type
            A unique string label for this provider, used in logging and
            sorting.
        provider_priority
            The numeric priority controlling invocation order.  Providers with
            higher priorities are initialised before those with lower values.
        """
        self._provider_type = provider_type
        self._provider_priority = provider_priority

    def get_context_provider_priority(self) -> int:
        """Return the provider's numeric priority.

        Returns
        -------
        int
            The priority assigned at construction time.
        """
        return self._provider_priority

    def get_context_provider_type(self) -> str:
        """Return the provider's type identifier.

        Returns
        -------
        str
            The unique type name assigned at construction time.
        """
        return self._provider_type

    @abstractmethod
    def add_argparser_arguments(
        self, parser: argparse.ArgumentParser,
        **kwargs: Any,
    ) -> None:
        """Register command-line arguments that configure the provider.

        Parameters
        ----------
        parser
            The :class:`argparse.ArgumentParser` instance that should receive
            additional arguments.

        Notes
        -----
        Providers may add optional or required arguments.  When invoked, the
        parsed argument namespace will be passed to :meth:`init` as keyword
        arguments.  If a provider does not require CLI arguments it should
        leave the parser untouched.
        """

    @abstractmethod
    def init(self, **kwargs: Any) -> GenomicContext | None:
        """Build a genomic context using the provided configuration.

        Parameters
        ----------
        **kwargs
            Keyword arguments typically derived from command-line parsing,
            environment variables, or configuration files.  The exact keys
            depend on what the provider declared in
            :meth:`add_argparser_arguments`.

        Returns
        -------
        GenomicContext | None
            A new context instance if the provider successfully assembled the
            required resources, or ``None`` if the provider chooses to abstain
            (for example when optional arguments are omitted).

        Notes
        -----
        Returning ``None`` allows a provider to conditionally participate.
        Other providers may then supply default or fallback contexts.
        """


class SimpleGenomicContext(GenomicContext):
    """Dictionary-backed implementation of :class:`GenomicContext`.

    This concrete context stores resource objects in a simple dictionary and
    returns them on demand.  It is commonly used by providers that assemble a
    fixed set of resources at initialization time.

    Parameters
    ----------
    context_objects
        A mapping from string keys to resource objects.  Typical keys include
        :const:`GC_GRR_KEY`, :const:`GC_REFERENCE_GENOME_KEY`,
        :const:`GC_GENE_MODELS_KEY`, and :const:`GC_ANNOTATION_PIPELINE_KEY`.
    source
        A human-readable label identifying the origin of this context, such as
        a provider name or file path.

    Attributes
    ----------
    _context : dict[str, Any]
        The internal dictionary holding the resource objects.
    _source : str
        The stored source label.
    """

    def __init__(
        self, context_objects: dict[str, Any],
        source: str,
    ):
        self._context: dict[str, Any] = context_objects
        self._source = source

    def get_context_object(self, key: str) -> Any | None:
        """Retrieve a resource by key.

        Parameters
        ----------
        key
            The string identifier of the desired resource.

        Returns
        -------
        Any | None
            The stored object if the key exists, otherwise ``None``.
        """
        return self._context.get(key)

    def get_context_keys(self) -> set[str]:
        """Report all available keys.

        Returns
        -------
        set[str]
            The set of keys under which resources are stored.
        """
        return set(self._context.keys())

    def get_source(self) -> str:
        """Return the source label.

        Returns
        -------
        str
            The human-readable identifier assigned at construction time.
        """
        return self._source


class PriorityGenomicContext(GenomicContext):
    """Composite context implementing priority-based fallback lookup.

    This context merges multiple underlying contexts, consulting them in order
    when a resource is requested.  The first context that provides a non-None
    value for a given key wins.  This strategy allows CLI or user-supplied
    contexts to override defaults from configuration-driven providers.

    Parameters
    ----------
    contexts
        An iterable of :class:`GenomicContext` instances, ordered by
        descending precedence.  When a resource is requested, the priority
        context walks the sequence and returns the first non-None result.

    Attributes
    ----------
    contexts : Iterable[GenomicContext]
        The ordered collection of underlying contexts.

    Notes
    -----
    At construction time the context logs the sources of all constituent
    contexts to aid debugging.  If no contexts are provided a warning is
    logged to indicate that no resources will be available.
    """

    def __init__(self, contexts: Iterable[GenomicContext]):
        self.contexts = contexts
        if self.contexts:
            logger.debug("Using the following genomic context:")
            for context in self.contexts:
                logger.debug("\t%s", context.get_source())
        else:
            logger.debug("No genomic contexts are available.")

    def get_context_object(self, key: str) -> Any | None:
        """Retrieve a resource using priority-based fallback.

        Parameters
        ----------
        key
            The string identifier of the desired resource.

        Returns
        -------
        Any | None
            The first non-None object found among the underlying contexts, or
            ``None`` if every context returns ``None`` (or if no contexts are
            available).

        Notes
        -----
        Each context is queried in order.  When a context returns a non-None
        value the search stops and that value is returned.  A log entry is
        generated to identify which context supplied the object.
        """
        for context in self.contexts:
            obj = context.get_context_object(key)
            if obj:
                logger.info(
                    "object with key %s found in the context %s",
                    key, context.get_source())
                return obj
        return None

    def get_context_keys(self) -> set[str]:
        """Compute the union of all keys from underlying contexts.

        Returns
        -------
        set[str]
            The merged set of keys available across all constituent contexts.
            If multiple contexts expose the same key the set contains it only
            once.
        """
        result: set[str] = set()
        for context in self.contexts:
            result = result.union(context.get_context_keys())
        return result

    def get_source(self) -> str:
        """Generate a composite source identifier.

        Returns
        -------
        str
            A string of the form
            ``"PriorityGenomicContext(source1|source2|...)"`` listing the
            sources of all underlying contexts in priority order.
        """
        result = []
        result = [str(context.get_source()) for context in self.contexts]
        return f"PriorityGenomicContext({'|'.join(result)})"
