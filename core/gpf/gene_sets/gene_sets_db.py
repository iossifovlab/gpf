"""Class for handling a database of gene set collections."""
from __future__ import annotations

import logging
from collections.abc import Sequence
from functools import cached_property
from typing import Any

from gain.gene_sets.gene_set import BaseGeneSetCollection, GeneSet

logger = logging.getLogger(__name__)


class GeneSetsDb:
    """Class that represents a dictionary of gene set collections."""

    def __init__(
        self,
        gene_set_collections: Sequence[BaseGeneSetCollection],
    ) -> None:
        self.gene_set_collections: dict[str, BaseGeneSetCollection] = {
            gsc.collection_id: gsc.load()
            for gsc in gene_set_collections
        }

    @cached_property
    def collections_descriptions(self) -> list[dict[str, Any]]:
        """Collect gene set descriptions.

        Iterates and creates a list of descriptions
        for each gene set collection
        """
        gene_sets_collections_desc = []
        for gsc in self.gene_set_collections.values():
            label = gsc.web_label
            format_str = gsc.web_format_str
            gsc_id = gsc.collection_id
            if not label or not format_str:
                continue
            gene_sets_collections_desc.append(
                {
                    "desc": label,
                    "name": gsc_id,
                    "format": format_str.split("|"),
                },
            )
        return gene_sets_collections_desc

    def has_gene_set_collection(self, gsc_id: str) -> bool:
        """Check the database if contains the specified gene set collection."""
        return gsc_id in self.gene_set_collections

    def get_gene_set_collection_ids(self) -> set[str]:
        """Return all gene set collection ids.

        Including the ids of collections which have not been loaded.
        """
        return set(self.gene_set_collections.keys())

    def get_gene_set_ids(self, collection_id: str) -> set[str]:
        """Return the IDs of all the gene sets in specified collection."""
        gsc = self.gene_set_collections[collection_id]
        return set(gsc.gene_sets.keys())

    def get_all_gene_sets(self, collection_id: str) -> list[GeneSet]:
        """Return all the gene sets in the specified collection."""
        gsc = self.gene_set_collections[collection_id]
        logger.debug(
            "gene sets from %s: %s", collection_id, len(gsc.gene_sets.keys()))
        return gsc.get_all_gene_sets()

    def get_gene_set(
        self, collection_id: str,
        gene_set_id: str,
    ) -> GeneSet | None:
        """Find and return a gene set in a gene set collection."""
        gsc = self.gene_set_collections[collection_id]
        return gsc.get_gene_set(gene_set_id)

    def __len__(self) -> int:
        return len(self.gene_set_collections)
