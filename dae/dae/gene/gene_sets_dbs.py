from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set import DenovoGeneSet


class GeneSetsDb:

    def get_gene_set_collections_ids():
        pass

    def get_gene_set_ids():
        pass

    def get_gene_set():
        pass

    def load_gene_set_from_file():
        pass


class DenovoGeneSetsDb:

    def __init__(self, variants_db):
        self.variants_db = variants_db
        self._denovo_gene_set_cache_values = dict()
        self._denovo_gene_set_config_cache_values = dict()

    def __len__(self):
        return len(self._denovo_gene_set_cache)

    @property
    def _denovo_gene_set_cache(self):
        if not self._denovo_gene_set_cache_values:
            self._load_cache()
        return self._denovo_gene_set_cache_values

    @property
    def _denovo_gene_set_config_cache(self):
        if not self._denovo_gene_set_config_cache_values:
            self._load_cache()
        return self._denovo_gene_set_config_cache_values

    @staticmethod
    def _get_gene_sets_types(gene_sets_types, permitted_datasets):
        return {
            k: {pg_id: v for pg_id, v in pg.items() if v}
            for k, pg in gene_sets_types.items()
            if permitted_datasets is None or k in permitted_datasets
        }

    def _load_cache(self):
        gene_set_ids = set(self.variants_db.get_all_ids())
        for denovo_gene_set_id in gene_set_ids:
            self._load_denovo_gene_set_in_cache(denovo_gene_set_id)

    def _load_denovo_gene_set_in_cache(self, denovo_gene_set_id):
        study = self.variants_db.get(denovo_gene_set_id)
        denovo_gene_set_config = DenovoGeneSetConfigParser.parse(
            self.variants_db.get_config(denovo_gene_set_id)
        )
        if not (study and denovo_gene_set_config):
            return

        denovo_gene_set = DenovoGeneSet(study, denovo_gene_set_config)
        denovo_gene_set.load()

        self._denovo_gene_set_config_cache_values[denovo_gene_set_id] = \
            denovo_gene_set_config
        self._denovo_gene_set_cache_values[denovo_gene_set_id] = \
            denovo_gene_set

    def _build_cache(self, gene_set_ids=None):
        for dgs_id, dgs in self._denovo_gene_set_cache.items():
            if gene_set_ids and dgs_id not in gene_set_ids:
                continue
            dgs.build_cache()

    def get_descriptions(self, permitted_datasets=None):
        gene_sets_types = []
        for denovo_gene_set_id, denovo_gene_set in \
                self._denovo_gene_set_cache.items():
            if permitted_datasets is None or \
                    denovo_gene_set_id in permitted_datasets:
                gene_sets_types += denovo_gene_set.get_gene_sets_types_legend()

        return {
            'desc': 'Denovo',
            'name': 'denovo',
            'format':  ['key', ' (|count|)'],
            'types': gene_sets_types,
        }

    def get_genotype_data_ids(self):
        return set(self._denovo_gene_set_cache.keys())

    def get_gene_set_ids(self, genotype_data_id):
        return self._denovo_gene_set_config_cache[genotype_data_id].\
            gene_sets_names

    def get_gene_set(self, gene_set_id, denovo_gene_set_spec,
                     permitted_datasets=None):
        denovo_gene_sets_types = self._get_gene_sets_types(
            denovo_gene_set_spec,
            permitted_datasets
        )

        return DenovoGeneSet.get_gene_set(
            gene_set_id,
            list(self._denovo_gene_set_cache.values()),
            denovo_gene_sets_types
        )

    def get_gene_sets(self, denovo_gene_set_spec, permitted_datasets=None):
        denovo_gene_sets_types = self._get_gene_sets_types(
            denovo_gene_set_spec,
            permitted_datasets
        )

        return DenovoGeneSet.get_gene_sets(
            list(self._denovo_gene_set_cache.values()),
            denovo_gene_sets_types
        )
