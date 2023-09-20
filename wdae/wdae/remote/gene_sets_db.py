"""Classes for handling of remote gene sets."""

import logging
from typing import Optional, List, Set, Dict, Any

from remote.rest_api_client import RESTClient

from dae.gene.gene_sets_db import GeneSet, GeneSetCollection, GeneSetsDb, \
    BaseGeneSetCollection

logger = logging.getLogger(__name__)


class RemoteGeneSetCollection(BaseGeneSetCollection):
    """Class for handling remote gene set collections."""

    def __init__(
        self, collection_id: str, rest_client: RESTClient, desc: str, fmt: str
    ):
        self.rest_client: RESTClient = rest_client
        self._remote_collection_id = collection_id
        self._remote_gene_sets_loaded = False
        self.remote_gene_sets_names: List[str] = []
        self.remote_gene_sets_desc: List[Dict[str, Any]] = []

        collection_id = self.rest_client.prefix_remote_identifier(
            collection_id
        )
        self.collection_id = collection_id
        self.collection_description: str = \
            self.rest_client.prefix_remote_name(desc)
        self.collection_format: str = fmt
        self.gene_sets: Dict[str, GeneSet] = {}

    def _load_remote_gene_sets(self):
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

    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        self._load_remote_gene_sets()
        if gene_set_id not in self.remote_gene_sets_names:
            logger.warning(
                "No such gene set '%s' available in remote client '%s'!",
                gene_set_id,
                self.rest_client.remote_id
            )
            return None

        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            raw_gene_set = self.rest_client.get_gene_set_download(
                self._remote_collection_id, gene_set_id
            ).split("\n")
            raw_gene_set = [gs.strip() for gs in raw_gene_set]
            raw_gene_set = [gs for gs in raw_gene_set if gs]
            whole_gene_set = raw_gene_set.pop(0).strip('\"').split(":")
            assert whole_gene_set is not None
            assert whole_gene_set[0] == gene_set_id
            description = whole_gene_set[1]
            gene_set = GeneSet(gene_set_id, description, raw_gene_set)
            self.gene_sets[gene_set_id] = gene_set

        return gene_set

    def get_all_gene_sets(self) -> List[GeneSet]:
        self._load_remote_gene_sets()
        for gene_set_name in self.remote_gene_sets_names:
            self.get_gene_set(gene_set_name)
        return list(self.gene_sets.values())


class RemoteGeneSetsDb(GeneSetsDb):
    """Class for handling remote gene sets."""

    def __init__(
        self, remote_clients: List[RESTClient], local_gene_sets_db: GeneSetsDb
    ):
        super().__init__([])
        self._local_gsdb: GeneSetsDb = local_gene_sets_db
        self.gene_set_collections: Dict[str, GeneSetCollection] = {}
        self.remote_clients: List[RESTClient] = remote_clients
        self._load_remote_collections()

    def _load_remote_collections(self):
        for remote_client in self.remote_clients:
            for collection in remote_client.get_gene_set_collections():
                gsc_id = collection["name"]
                if gsc_id == "denovo":
                    continue
                gsc_desc = collection["desc"]
                gsc_fmt = collection["format"]
                gsc = RemoteGeneSetCollection(
                    gsc_id, remote_client, gsc_desc, gsc_fmt
                )
                gsc_id = gsc.collection_id
                self.gene_set_collections[gsc_id] = gsc

    @property  # type: ignore
    def collections_descriptions(self):
        gene_sets_collections_desc = list(
            self._local_gsdb.collections_descriptions
        )
        for gsc in self.gene_set_collections.values():
            gene_sets_collections_desc.append(
                {
                    "desc": gsc.collection_description,
                    "name": gsc.collection_id,
                    "format": gsc.collection_format,
                    "types": [],
                }
            )
        return gene_sets_collections_desc

    def has_gene_set_collection(self, gsc_id: str) -> bool:
        return self._local_gsdb.has_gene_set_collection(gsc_id) \
            or gsc_id in self.gene_set_collections

    def get_gene_set_collection_ids(self) -> Set[str]:
        """Return all gene set collection ids.

        Including the ids of collections which have not been loaded.
        """
        return set(self.gene_set_collections.keys()).union(
            set(self._local_gsdb.get_gene_set_collection_ids()))

    def get_gene_set_ids(self, collection_id: str) -> Set[str]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_gene_set_ids(collection_id)
        return set(
            self.gene_set_collections[collection_id].gene_sets.keys()
        )

    def get_all_gene_sets(self, collection_id: str) -> List[GeneSet]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_all_gene_sets(collection_id)
        return list(
            self.gene_set_collections[collection_id].get_all_gene_sets()
        )

    def get_gene_set(
            self, collection_id: str, gene_set_id: str) -> Optional[GeneSet]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_gene_set(collection_id, gene_set_id)
        return self.gene_set_collections[
            collection_id
        ].get_gene_set(gene_set_id)
