from dae.gpf_instance.gpf_instance import GPFInstance

from dae.gene.gene_set_collections import GeneSetsCollections
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade

from dae.enrichment_tool.background_facade import BackgroundFacade

from .models import Dataset

from threading import Lock


__all__ = ['get_studies_manager']


class StudiesManager(object):

    def __init__(self, gpf_instance=None):
        if gpf_instance is None:
            gpf_instance = GPFInstance()
        self.gpf_instance = gpf_instance

        self.dae_config = gpf_instance.dae_config
        self.vdb = self.gpf_instance.variants_db

        self.scores_factory = self.gpf_instance.scores_factory
        self.gene_info_config = self.gpf_instance.gene_info_config
        self.weights_factory = self.gpf_instance.weights_factory

        self.gene_sets_collections = None
        self.common_report_facade = gpf_instance.common_report_facade

        self.reload_datasets()

    def reload_datasets(self):
        for study_id in self.vdb.get_all_ids():
            Dataset.recreate_dataset_perm(study_id, [])

        self.gene_sets_collections = GeneSetsCollections(
            self.vdb, self.gene_info_config)
        self.denovo_gene_set_facade = DenovoGeneSetFacade(self.vdb)

        self.background_facade = BackgroundFacade(self.vdb)

    def get_variants_db(self):
        return self.vdb

    def get_common_report_facade(self):
        return self.common_report_facade

    def get_gene_info_config(self):
        return self.gene_info_config

    def get_scores_factory(self):
        assert self.scores_factory is not None
        return self.scores_factory

    def get_weights_factory(self):
        return self.weights_factory

    def get_gene_sets_collections(self):
        return self.gene_sets_collections

    def get_denovo_gene_set_facade(self):
        return self.denovo_gene_set_facade

    def get_background_facade(self):
        return self.background_facade

    def get_permission_denied_prompt(self):
        return self.dae_config.gpfjs.permission_denied_prompt


_studies_manager = None
_studies_manager_lock = Lock()


def get_studies_manager():
    global _studies_manager
    global _studies_manager_lock

    if _studies_manager is None:
        _studies_manager_lock.acquire()
        try:
            if _studies_manager is None:
                sm = StudiesManager()
                _studies_manager = sm
        finally:
            _studies_manager_lock.release()

    return _studies_manager
