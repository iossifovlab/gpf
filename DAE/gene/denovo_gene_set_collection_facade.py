from gene.config import DenovoGeneSetCollectionConfig
from gene.gene_set_collections import DenovoGeneSetsCollection


class DenovoGeneSetCollectionFacade(object):

    def __init__(self, variants_db):
        self._denovo_gene_set_cache = {}
        self._denovo_gene_set_config_cache = {}

        self.variants_db = variants_db

    def get_collections_descriptions(self, permitted_datasets=None):
        self.load_cache()

        gene_sets_types = []
        for denovo_gene_set_id, denovo_genen_set in \
                self._denovo_gene_set_cache.items():
            if permitted_datasets is None or \
                    denovo_gene_set_id in permitted_datasets:
                gene_sets_types += \
                    denovo_genen_set.get_gene_sets_types_legend()

        gene_sets_collections_desc = (
            {
                'desc': 'Denovo',
                'name': 'denovo',
                'format':  ['key', ' (|count|)'],
                'types': gene_sets_types,
            }
        )

        return gene_sets_collections_desc

    @staticmethod
    def _get_gene_sets_types(
            denovo_gene_set_id, gene_sets_types, permitted_datasets):
        denovo_gene_sets_types = gene_sets_types.get(denovo_gene_set_id, None)

        if denovo_gene_sets_types and \
            (permitted_datasets is None or
             denovo_gene_set_id in permitted_datasets):

            return {
                denovo_gene_set_id: {
                    k: pg
                    for k, pg in denovo_gene_sets_types.items() if pg
                }
            }

        return None

    def get_denovo_gene_set(
            self, gene_sets_collection_id, denovo_gene_set_id,
            gene_sets_types={}, permitted_datasets=None):
        assert gene_sets_collection_id == 'denovo'

        self.load_cache()

        result = []
        for denovo_gene_set_id, denovo_gene_set in \
                self._denovo_gene_set_cache.items():
            denovo_gene_sets_types = self._get_gene_sets_types(
                denovo_gene_set_id, gene_sets_types, permitted_datasets)

            if denovo_gene_sets_types is not None:
                result.append(
                    denovo_gene_set.get_gene_set(
                        gene_sets_collection_id, gene_sets_types
                    )
                )

        return result[0]

    def get_denovo_gene_sets(
            self, gene_sets_collection_id, gene_sets_types={},
            permitted_datasets=None, load=True):
        assert gene_sets_collection_id == 'denovo'

        self.load_cache()

        result = []
        for denovo_gene_set_id, denovo_gene_set in \
                self._denovo_gene_set_cache.items():
            denovo_gene_sets_types = self._get_gene_sets_types(
                denovo_gene_set_id, gene_sets_types, permitted_datasets)
            print(gene_sets_types)
            if denovo_gene_sets_types is not None:
                result.append(denovo_gene_set.get_gene_sets(gene_sets_types))

        return result[0]

    def get_denovo_gene_set_config(self, denovo_gene_set_id):
        self.load_cache({denovo_gene_set_id})

        if denovo_gene_set_id not in self._denovo_gene_set_config_cache:
            return None

        return self._denovo_gene_set_config_cache[denovo_gene_set_id]

    def get_all_denovo_gene_set_configs(self):
        self.load_cache()

        return list(self._denovo_gene_set_config_cache.values())

    def get_all_denovo_gene_set_ids(self):
        self.load_cache()

        return [
            config.id for config in self._denovo_gene_set_config_cache.values()
        ]

    def has_denovo_gene_set(self, denovo_gene_set_id):
        assert denovo_gene_set_id == 'denovo'

        self.load_cache()

        return len(self._denovo_gene_set_cache) != 0

    def load_cache(self, denovo_gene_set_ids=None, load=True):
        if denovo_gene_set_ids is None:
            denovo_gene_set_ids = set(self.variants_db.get_all_ids())

        assert isinstance(denovo_gene_set_ids, set)

        cached_ids = set(self._denovo_gene_set_config_cache.keys())
        if denovo_gene_set_ids != cached_ids:
            to_load = denovo_gene_set_ids - cached_ids
            for denovo_gene_set_id in to_load:
                self._load_denovo_gene_set_config_in_cache(denovo_gene_set_id)
                self._load_denovo_gene_set_in_cache(denovo_gene_set_id, load)

    def _load_denovo_gene_set_config_in_cache(self, denovo_gene_set_id):
        denovo_gene_set_config = DenovoGeneSetCollectionConfig.from_config(
            self.variants_db.get_config(denovo_gene_set_id))
        if denovo_gene_set_config is None:
            return

        self._denovo_gene_set_config_cache[denovo_gene_set_id] = \
            denovo_gene_set_config

    def _load_denovo_gene_set_in_cache(self, denovo_gene_set_id, load=True):
        self._load_denovo_gene_set_config_in_cache(denovo_gene_set_id)

        if denovo_gene_set_id not in self._denovo_gene_set_config_cache:
            return

        study = self.variants_db.get(denovo_gene_set_id)
        if study is None:
            return
        denovo_gene_set_config = \
            self._denovo_gene_set_config_cache[denovo_gene_set_id]

        gsc = DenovoGeneSetsCollection(study, denovo_gene_set_config)
        if load:
            gsc.load()

        self._denovo_gene_set_cache[denovo_gene_set_id] = gsc
