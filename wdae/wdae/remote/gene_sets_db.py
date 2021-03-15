from typing import List

from dae.gene.gene_sets_db import GeneSet, GeneSetCollection, GeneSetsDb
from dae.utils.dae_utils import cached
from remote.rest_api_client import RESTClient


class RemoteGeneSetCollection(GeneSetCollection):
    rest_client: RESTClient
    remote_gene_sets: List[str]

    def __init__(self, collection_id: str, rest_client: RESTClient):
        self.rest_client = rest_client
        self.remote_gene_sets = [
            rgs["name"] for rgs in rest_client.get_gene_sets(collection_id)
        ]
        super().__init__(collection_id, list())
    
    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        if gene_set_id not in self.remote_gene_sets:
            print(f"No such gene set '{gene_set_id}' available in remote"
                  f" client '{self.rest_client.remote_id}'!")
            return None

        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            raw_gene_set = self.rest_client.get_gene_set_download(
                self.collection_id, gene_set_id
            ).split("\n")
            description = raw_gene_sets.pop(0)
            gene_set = GeneSet(gene_set_id, desc, raw_gene_set)
            self.gene_sets[gene_set_id] = gene_set

        return gene_set


class RemoteGeneSetsDb(GeneSetsDb):
    def __init__(self, remote_clients, local_gene_sets_db):
        self._local_gsdb = local_gene_sets_db
        self.remote_clients = remote_clients

        self._load_remote_collections()

    def _load_remote_collections(self):
        raise NotImplementedError()

    @staticmethod
    def _produce_gene_terms(self, collection_id):
        raise NotImplementedError()

    @property  # type: ignore
    @cached
    def collections_descriptions(self):
        raise NotImplementedError()

    @staticmethod
    def load_gene_set_from_file(filename, config):
        raise NotImplementedError()

    def _load_gene_set_collection(self, gene_sets_collection_id):
        raise NotImplementedError()

    def has_gene_set_collection(self, gsc_id):
        raise NotImplementedError()

    def get_gene_set_collection_ids(self):
        """
        Return all gene set collection ids (including the ids
        of collections which have not been loaded).
        """
        raise NotImplementedError()

    def get_gene_set_ids(self, collection_id):
        raise NotImplementedError()

    def get_all_gene_sets(self, collection_id):
        raise NotImplementedError()

    def get_gene_set(self, collection_id, gene_set_id):
        raise NotImplementedError()