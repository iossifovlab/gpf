"""Classes for handling of remote gene sets."""

import logging
from functools import cached_property
from typing import Any

from dae.gene_sets.gene_sets_db import (
    BaseGeneSetCollection,
    GeneSet,
    GeneSetsDb,
)

from federation.rest_api_client import RESTClient

logger = logging.getLogger(__name__)


class RemoteGeneSetCollection(BaseGeneSetCollection):
    """Class for handling remote gene set collections."""

    def __init__(
        self, collection_id: str, rest_client: RESTClient, desc: str, fmt: str,
    ):
        self.rest_client: RESTClient = rest_client
        self._remote_collection_id = collection_id
        self._remote_gene_sets_loaded = False
        self.remote_gene_sets_names: list[str] = []
        self.remote_gene_sets_desc: list[dict[str, Any]] = []

        collection_id = self.rest_client.prefix_remote_identifier(
            collection_id,
        )
        self.collection_id = collection_id
        self.web_label = \
            self.rest_client.prefix_remote_name(desc)
        self.web_format_str = fmt
        self.gene_sets: dict[str, GeneSet] = {}

    def _load_remote_gene_sets(self) -> None:
        if self._remote_gene_sets_loaded:
            return

        remote_gene_sets_desc = self.rest_client.get_gene_sets(
            self._remote_collection_id)
        if remote_gene_sets_desc is None:
            raise ValueError("unable to load remote gene sets")
        self.remote_gene_sets_desc = remote_gene_sets_desc

        self.remote_gene_sets_names = [
            rgs["name"] for rgs in self.remote_gene_sets_desc
        ]

        self._remote_gene_sets_loaded = True

    def get_gene_set(self, gene_set_id: str) -> GeneSet | None:
        self._load_remote_gene_sets()
        if gene_set_id not in self.remote_gene_sets_names:
            logger.warning(
                "No such gene set '%s' available in remote client '%s'!",
                gene_set_id,
                self.rest_client.remote_id,
            )
            return None

        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None or len(gene_set.syms) != gene_set.count:
            raw_gene_set = self.rest_client.get_gene_set_download(
                self._remote_collection_id, gene_set_id,
            ).split("\n")
            raw_gene_set = [gs.strip() for gs in raw_gene_set]
            raw_gene_set = [gs for gs in raw_gene_set if gs]
            name = raw_gene_set.pop(0).strip('"')
            name = name.strip()
            description = raw_gene_set.pop(0).strip('"')
            description = description.strip()
            assert name is not None
            assert description is not None
            assert name == gene_set_id, (name, gene_set_id)
            gene_set = GeneSet(gene_set_id, description, raw_gene_set)
            self.gene_sets[gene_set_id] = gene_set

        return gene_set

    def get_all_gene_sets(self) -> list[GeneSet]:
        self._load_remote_gene_sets()
        gene_set_descriptions = self.rest_client.get_gene_sets(
            self._remote_collection_id,
        )
        if gene_set_descriptions is None:
            return []
        for gene_set_description in gene_set_descriptions:
            name = gene_set_description.get("name")
            desc = gene_set_description.get("description", "")
            count = gene_set_description.get("count")
            if name is not None and count is not None:
                gene_set = GeneSet(name, desc, [])
                # Override count, syms will be loaded later
                gene_set.count = count
                self.gene_sets[name] = gene_set
        return list(self.gene_sets.values())


class RemoteGeneSetsDb(GeneSetsDb):
    """Class for handling remote gene sets."""

    def __init__(
        self, remote_clients: dict[str, RESTClient],
        local_gene_sets_db: GeneSetsDb,
    ):
        super().__init__([])
        self._local_gsdb: GeneSetsDb = local_gene_sets_db
        self.gene_set_collections = {}
        self.remote_clients: list[RESTClient] = list(remote_clients.values())
        self._load_remote_collections()

    def _load_remote_collections(self) -> None:
        for remote_client in self.remote_clients:
            for collection in remote_client.get_gene_set_collections():
                gsc_id = collection["name"]
                if gsc_id == "denovo":
                    continue
                gsc_desc = collection["desc"]
                gsc_fmt = "|".join(collection["format"])
                gsc = RemoteGeneSetCollection(
                    gsc_id, remote_client, gsc_desc, gsc_fmt,
                )
                gsc_id = gsc.collection_id
                self.gene_set_collections[gsc_id] = gsc

    @cached_property
    def collections_descriptions(self) -> list[dict[str, Any]]:
        gene_sets_collections_desc = list(
            self._local_gsdb.collections_descriptions,
        )
        for gsc in self.gene_set_collections.values():
            gene_sets_collections_desc.append(  # noqa: PERF401
                {
                    "desc": gsc.web_label,
                    "name": gsc.collection_id,
                    "format": gsc.web_format_str.split("|"),
                    "types": [],
                },
            )
        return gene_sets_collections_desc

    def has_gene_set_collection(self, gsc_id: str) -> bool:
        return self._local_gsdb.has_gene_set_collection(gsc_id) \
            or gsc_id in self.gene_set_collections

    def get_gene_set_collection_ids(self) -> set[str]:
        """Return all gene set collection ids.

        Including the ids of collections which have not been loaded.
        """
        return set(self.gene_set_collections.keys()).union(
            set(self._local_gsdb.get_gene_set_collection_ids()))

    def get_gene_set_ids(self, collection_id: str) -> set[str]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_gene_set_ids(collection_id)
        return set(
            self.gene_set_collections[collection_id].gene_sets.keys(),
        )

    def get_all_gene_sets(self, collection_id: str) -> list[GeneSet]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_all_gene_sets(collection_id)
        return list(
            self.gene_set_collections[collection_id].get_all_gene_sets(),
        )

    def get_gene_set(
            self, collection_id: str, gene_set_id: str) -> GeneSet | None:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_gene_set(collection_id, gene_set_id)
        return self.gene_set_collections[
            collection_id
        ].get_gene_set(gene_set_id)
