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
    """Defines annotation pipeline genomics context provider."""

    def add_argparser_arguments(
        self, parser: argparse.ArgumentParser,
    ) -> None:
        """Add command line arguments to the argument parser."""
        parser.add_argument(
            "--genotype-storage-config", "--gsf",
            dest=GC_GENOTYPE_STORAGES_KEY,
            default=None,
            help="genotype storages configuration file")

    def init(
        self,
        **kwargs: Any,
    ) -> GenomicContext | None:
        """Build a CLI genotype storages genomic context."""

        context_objects = {}

        if kwargs.get(GC_GENOTYPE_STORAGES_KEY):
            logger.info(
                "Using the genotype storages from the file %s.",
                kwargs[GC_GENOTYPE_STORAGES_KEY])
            storage_configs = yaml.safe_load(
                pathlib.Path(kwargs[GC_GENOTYPE_STORAGES_KEY]).read_text())
            registry = GenotypeStorageRegistry()
            registry.register_storage_config(storage_configs)
            context_objects[GC_GENOTYPE_STORAGES_KEY] = registry
            return SimpleGenomicContext(
                context_objects, source="CLIGenotypeStorageContextProvider")
        return None


def get_context_genotype_storages(
    context: GenomicContext,
) -> GenotypeStorageRegistry | None:
    """Get genotype storage registry from genomic context."""
    registry = context.get_context_object(GC_GENOTYPE_STORAGES_KEY)
    if registry is None:
        return None
    if not isinstance(registry, GenotypeStorageRegistry):
        raise TypeError(
            f"The genotype storage registry from the genomic "
            f" context is not an GenotypeStorageRegistry: {type(registry)}")
    return registry
