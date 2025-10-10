"""Command-line helpers for genotype storage registry configuration.

This module provides CLI-based integration of genotype storage registries
into the genomic context system.  The
:class:`CLIGenotypeStorageContextProvider` allows tools to accept a genotype
storage configuration file via command-line arguments and exposes the
resulting :class:`GenotypeStorageRegistry` through the shared genomic
context mechanism.

Key Constants
-------------
GC_GENOTYPE_STORAGES_KEY : str
    Standard key for the genotype storage registry object in the context.

See Also
--------
dae.genomic_resources.genomic_context
    High-level orchestration and provider registration functions.
dae.genotype_storage.genotype_storage_registry.GenotypeStorageRegistry
    The registry implementation for managing multiple genotype storages.
"""
from __future__ import annotations

import argparse
import logging
import pathlib
from typing import Any

import yaml

from dae.genomic_resources.genomic_context_base import (
    GenomicContext,
    GenomicContextProvider,
    SimpleGenomicContext,
)
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)

logger = logging.getLogger(__name__)
GC_GENOTYPE_STORAGES_KEY = "genotype_storages"


class CLIGenotypeStorageContextProvider(GenomicContextProvider):
    """Expose genotype storage registry configuration via CLI.

    This provider allows CLI tools to load a genotype storage registry from a
    YAML configuration file specified on the command line.  When invoked
    without the ``--genotype-storage-config`` argument, the provider returns
    ``None`` to allow other providers to supply default storage registries.

    The provider registers a single context key,
    :const:`GC_GENOTYPE_STORAGES_KEY`, pointing to the instantiated
    :class:`GenotypeStorageRegistry`.

    Notes
    -----
    The provider has a priority of 500, placing it below general resource
    providers (like CLI genomic context at 900) but above lower-priority
    specialized providers.
    """

    def __init__(
            self,
    ) -> None:
        """Initialise the provider with its identifier and priority."""
        super().__init__(
            "CLIGenotypeStorageContextProvider",
            500,
        )

    def add_argparser_arguments(
        self, parser: argparse.ArgumentParser,
    ) -> None:
        """Register CLI argument for the genotype storage configuration file.

        Parameters
        ----------
        parser
            The argument parser that should receive the provider-specific
            option.

        Notes
        -----
        The provider adds ``--genotype-storage-config`` (short form ``--gsf``)
        pointing to a YAML file describing the genotype storage
        configurations.
        """
        parser.add_argument(
            "--genotype-storage-config", "--gsf",
            dest=GC_GENOTYPE_STORAGES_KEY,
            default=None,
            help="genotype storages configuration file")

    def init(
        self,
        **kwargs: Any,
    ) -> GenomicContext | None:
        """Build a genomic context containing a genotype storage registry.

        Parameters
        ----------
        **kwargs
            Keyword arguments parsed from the command line.  The provider
            inspects the ``genotype_storages`` key (set via
            ``--genotype-storage-config``).

        Returns
        -------
        GenomicContext | None
            A context exposing the genotype storage registry under
            :const:`GC_GENOTYPE_STORAGES_KEY`, or ``None`` when the
            configuration file argument is absent.

        Notes
        -----
        The configuration file must be valid YAML defining one or more genotype
        storage entries.  The provider loads the file, instantiates a
        :class:`GenotypeStorageRegistry`, and registers the configured
        storages.
        """

        context_objects = {}

        if kwargs.get(GC_GENOTYPE_STORAGES_KEY):
            logger.info(
                "Using the genotype storages from the file %s.",
                kwargs[GC_GENOTYPE_STORAGES_KEY])
            storage_configs = yaml.safe_load(
                pathlib.Path(kwargs[GC_GENOTYPE_STORAGES_KEY]).read_text())
            registry = GenotypeStorageRegistry()
            if "storages" in storage_configs:
                registry.register_storages_configs(storage_configs)
            elif "storage_type" in storage_configs:
                registry.register_storage_config(storage_configs)
            else:
                raise ValueError(
                    "Unexpected format of genotype storage configuration.")

            context_objects[GC_GENOTYPE_STORAGES_KEY] = registry
            return SimpleGenomicContext(
                context_objects, source="CLIGenotypeStorageContextProvider")
        return None


def get_context_genotype_storages(
    context: GenomicContext,
) -> GenotypeStorageRegistry | None:
    """Extract a validated genotype storage registry from *context*.

    Parameters
    ----------
    context
        The genomic context from which to retrieve the registry object.

    Returns
    -------
    GenotypeStorageRegistry | None
        The registry instance or ``None`` when the context does not expose a
        genotype storage registry.

    Raises
    ------
    TypeError
        If the context entry is present but does not contain the expected
        :class:`GenotypeStorageRegistry` type.

    Notes
    -----
    This helper is analogous to
    :func:`dae.annotation.annotation_genomic_context_cli.get_context_pipeline`
    and provides type-safe access to the genotype storage registry within the
    context system.
    """
    registry = context.get_context_object(GC_GENOTYPE_STORAGES_KEY)
    if registry is None:
        return None
    if not isinstance(registry, GenotypeStorageRegistry):
        raise TypeError(
            f"The genotype storage registry from the genomic "
            f"context is not an GenotypeStorageRegistry: {type(registry)}")
    return registry
