from dae.gene.gene_sets_db import GeneSetsDb


class RemoteGeneSetCollection:
    def __init__(self, rest_client, collection_id):
        assert collection_id != "denovo"
        self.gsc_id = collection_id


class RemoteGeneSetsDb(GeneSetsDb):
    def __init__(self, remote_clients, local_gene_sets_db):
        self._local_gsdb = local_gene_sets_db
        self.remote_clients = remote_clients

        self._load_remote_collections()

    def _load_remote_collections(self):
        pass

    @staticmethod
    def _produce_gene_terms(self, collection_id):
        pass
