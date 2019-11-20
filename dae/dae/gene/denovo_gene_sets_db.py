from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set import DenovoGeneSetCollection


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
    def _filter_spec(denovo_gene_set_spec, permitted_datasets):
        """
        Filter a denovo gene set spec to remove datasets which
        are not permitted for access and people groups with no
        specified values.
        """
        return {
            genotype_data_id: {pg_id: v for pg_id, v in pg.items() if v}
            for genotype_data_id, pg in denovo_gene_set_spec.items()
            if permitted_datasets is None
            or genotype_data_id in permitted_datasets
        }

    def _load_cache(self):
        genotype_data_ids = set(self.variants_db.get_all_ids())
        for id_ in genotype_data_ids:
            self._load_denovo_gene_set_in_cache(id_)

    def _load_denovo_gene_set_in_cache(self, genotype_data_id, build=False):
        study = self.variants_db.get(genotype_data_id)
        denovo_gene_set_config = DenovoGeneSetConfigParser.parse(study.config)

        if not (study and denovo_gene_set_config):
            return

        denovo_gene_set = DenovoGeneSetCollection(
            study, denovo_gene_set_config
        )
        denovo_gene_set.load(build)

        self._denovo_gene_set_config_cache_values[genotype_data_id] = \
            denovo_gene_set_config
        self._denovo_gene_set_cache_values[genotype_data_id] = \
            denovo_gene_set

    def _build_cache(self, genotype_data_ids):
        for genotype_data_id in genotype_data_ids:
            self._load_denovo_gene_set_in_cache(genotype_data_id, build=True)

    def get_gene_set_descriptions(self, permitted_datasets=None):
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
        denovo_gene_set_spec = self._filter_spec(
            denovo_gene_set_spec,
            permitted_datasets
        )

        return DenovoGeneSetCollection.get_gene_set(
            gene_set_id,
            list(self._denovo_gene_set_cache.values()),
            denovo_gene_set_spec
        )

    def get_all_gene_sets(self, denovo_gene_set_spec, permitted_datasets=None):
        denovo_gene_set_spec = self._filter_spec(
            denovo_gene_set_spec,
            permitted_datasets
        )

        return DenovoGeneSetCollection.get_gene_sets(
            list(self._denovo_gene_set_cache.values()),
            denovo_gene_set_spec
        )
