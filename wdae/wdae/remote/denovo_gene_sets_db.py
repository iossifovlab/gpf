import logging
from typing import List, Dict

from remote.rest_api_client import RESTClient

from dae.gene.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.gene.gene_sets_db import GeneSet


logger = logging.getLogger(__name__)


class RemoteDenovoGeneSetsCollection:
    """Represents remote de Novo gene sets collection."""

    rest_client: RESTClient
    collection_id: str
    collection_description: str
    collection_format: List[str]
    collection_types: List[Dict[str, str]]

    def __init__(self, rest_client: RESTClient):

        self.rest_client = rest_client
        self.denovo_collection = next(filter(
            lambda c: c["name"] == "denovo",
            rest_client.get_gene_set_collections()
        ))
        self.collection_id = rest_client.prefix_remote_identifier("denovo")
        self.collection_description = rest_client.prefix_remote_name(
            self.denovo_collection["desc"]
        )
        self.collection_format = self.denovo_collection["format"]
        self.collection_types = self.denovo_collection["types"]

    # pylint: disable=unused-argument
    def get_all_gene_sets(self, denovo_gene_set_spec, permitted_datasets=None):
        # TODO FIXME Utilise permitted datasets
        return self.rest_client.get_denovo_gene_sets(
            denovo_gene_set_spec
        )

    def get_gene_set(
            self, gene_set_id, denovo_gene_set_spec, permitted_datasets=None):
        """Find and return a de Novo gene set."""
        logger.debug(
            "going to ged remote gene set: %s; %s",
            gene_set_id, denovo_gene_set_spec)
        # TODO FIXME Utilise permitted datasets
        raw_gene_set = self.rest_client.get_denovo_gene_set(
            gene_set_id, denovo_gene_set_spec).split("\n")

        raw_gene_set = [gs.strip() for gs in raw_gene_set]

        description = raw_gene_set.pop(0)
        gene_set = GeneSet(gene_set_id, description, raw_gene_set)

        return gene_set


class RemoteDenovoGeneSetsDb:
    """Represents remote de Novo gene sets database."""

    _local_dgsdb: DenovoGeneSetsDb
    remote_clients: List[RESTClient]
    remote_denovo_gene_set_collections: Dict[
        str, RemoteDenovoGeneSetsCollection
    ]

    def __init__(
        self,
        remote_clients: List[RESTClient],
        local_denovo_gene_sets_db: DenovoGeneSetsDb
    ):
        self.remote_denovo_gene_set_collections = dict()
        self._local_dgsdb = local_denovo_gene_sets_db
        self.remote_clients = remote_clients

        self._load_remote_collections()

    def __len__(self):
        return len(self.remote_clients) + len(self._local_dgsdb)

    def reload(self):
        self.remote_denovo_gene_set_collections = {}
        self._load_remote_collections()

    def _load_remote_collections(self):
        for client in self.remote_clients:
            if not client.has_denovo_gene_sets():
                continue
            remote_collection = RemoteDenovoGeneSetsCollection(client)
            self.remote_denovo_gene_set_collections[
                remote_collection.collection_id
            ] = remote_collection

    def get_gene_set_descriptions(self, permitted_datasets=None):
        """Collect and return the de Novo gene sets descriptions."""
        result = [
            self._local_dgsdb.get_gene_set_descriptions(permitted_datasets)
        ]
        for collection in self.remote_denovo_gene_set_collections.values():
            # TODO Implement permitted datasets
            result.append({
                "desc": collection.collection_description,
                "name": collection.collection_id,
                "format": collection.collection_format,
                "types": collection.collection_types,
            })
        return result

    def get_gene_set(
        self,
        gene_set_id,
        denovo_gene_set_spec,
        permitted_datasets=None,
        collection_id="denovo",
    ):
        """Return a de Novo gene set."""
        if collection_id == "denovo":
            return self._local_dgsdb.get_gene_set(
                gene_set_id, denovo_gene_set_spec, permitted_datasets
            )
        else:
            return self.remote_denovo_gene_set_collections[
                collection_id
            ].get_gene_set(
                gene_set_id, denovo_gene_set_spec, permitted_datasets
            )

    def get_all_gene_sets(
        self,
        denovo_gene_set_spec,
        permitted_datasets=None,
        collection_id="denovo",
    ):
        """Return all de Novo gene sets."""
        if collection_id == "denovo":
            return self._local_dgsdb.get_all_gene_sets(
                denovo_gene_set_spec, permitted_datasets
            )
        else:
            return self.remote_denovo_gene_set_collections[
                collection_id
            ].get_all_gene_sets(denovo_gene_set_spec, permitted_datasets)
