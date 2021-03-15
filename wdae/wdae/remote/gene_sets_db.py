from typing import Optional, List, Set, Dict

from dae.gene.gene_sets_db import GeneSet, GeneSetCollection, GeneSetsDb
from remote.rest_api_client import RESTClient


class RemoteGeneSetCollection(GeneSetCollection):
    rest_client: RESTClient
    remote_gene_sets: List[str]

    def __init__(self, collection_id: str, rest_client: RESTClient):
        self.rest_client = rest_client
        self._remote_collection_id = collection_id
        self.remote_gene_sets = [
            rgs["name"] for rgs in rest_client.get_gene_sets(
                self._remote_collection_id
            )
        ]
        collection_id = self.rest_client.prefix_remote_identifier(
            collection_id
        )
        super().__init__(collection_id, list())

    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        if gene_set_id not in self.remote_gene_sets:
            print(f"No such gene set '{gene_set_id}' available in remote"
                  f" client '{self.rest_client.remote_id}'!")
            return None

        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            raw_gene_set = self.rest_client.get_gene_set_download(
                self._remote_collection_id, gene_set_id
            ).split("\n\r")
            description = raw_gene_set.pop(0)
            gene_set = GeneSet(gene_set_id, description, raw_gene_set)
            self.gene_sets[gene_set_id] = gene_set

        return gene_set


class RemoteGeneSetsDb(GeneSetsDb):
    _local_gsdb: GeneSetsDb
    remote_clients: List[RESTClient]

    def __init__(
        self, remote_clients: List[RESTClient], local_gene_sets_db: GeneSetsDb
    ):
        self._local_gsdb = local_gene_sets_db
        self.gene_set_collections: Dict[str, GeneSetCollection] = dict()
        self.remote_clients = remote_clients
        self._load_remote_collections()

    def _load_remote_collections(self):
        for remote_client in self.remote_clients:
            for collection in remote_client.get_gene_set_collections():
                gsc_id = collection["name"]
                gsc = RemoteGeneSetCollection(gsc_id, remote_client)
                gsc_id = gsc.collection_id
                self.gene_set_collections[gsc_id] = gsc

    @property  # type: ignore
    def collections_descriptions(self):
        return self._local_gsdb.collections_descriptions

    def has_gene_set_collection(self, gsc_id: str) -> bool:
        return self._local_gsdb.has_gene_set_collection(gsc_id) \
               or gsc_id in self.gene_set_collections

    def get_gene_set_collection_ids(self) -> Set[str]:
        """
        Return all gene set collection ids (including the ids
        of collections which have not been loaded).
        """
        return set(self.gene_set_collections.keys()) \
            + self._local_gsdb.get_gene_set_collection_ids()

    def get_gene_set_ids(self, collection_id: str) -> Set[str]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_gene_set_ids(collection_id)
        else:
            return set(
                self.gene_set_collections[collection_id].gene_sets.keys()
            )

    def get_all_gene_sets(self, collection_id: str) -> List[GeneSet]:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_all_gene_sets(collection_id)
        else:
            return list(
                self.gene_set_collections[collection_id].gene_sets.values()
            )

    def get_gene_set(self, collection_id: str, gene_set_id: str) -> GeneSet:
        if self._local_gsdb.has_gene_set_collection(collection_id):
            return self._local_gsdb.get_gene_set(collection_id, gene_set_id)
        else:
            return self.gene_set_collections[
                collection_id
            ].get_gene_set(gene_set_id)
