from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade


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
        self.old_api_instance = DenovoGeneSetFacade(variants_db)
        self.old_api_cache_loaded = False

    @property
    def old_api(self):
        if not self.old_api_cache_loaded:
            self.old_api_instance.load_cache()
            self.old_api_cache_loaded = True
        return self.old_api_instance

    def get_genotype_data_ids(self):
        return set(self.old_api._denovo_gene_set_cache.keys())

    def get_gene_set_ids(self, genotype_data_id):
        return self.old_api._denovo_gene_set_config_cache[genotype_data_id].\
            gene_sets_names

    def get_gene_set(self, gene_set_id, denovo_gene_set_spec):
        genotype_data_ids = denovo_gene_set_spec.keys()
        return self.old_api.get_denovo_gene_set(
            'denovo',
            gene_set_id,
            denovo_gene_set_spec,
            genotype_data_ids
        )
