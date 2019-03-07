from __future__ import unicode_literals
from builtins import object

from configurable_entities.configuration import DAEConfig

from studies.factory import VariantsDb

from datasets_api.models import Dataset


__all__ = ['get_studies_manager']


class StudiesManager(object):

    def __init__(self, dae_config=None):
        if dae_config is None:
            dae_config = DAEConfig()
        self.dae_config = dae_config
        self.vdb = None

    def reload_dataset(self):
        self.vdb = VariantsDb(self.dae_config)

        for dataset_id in self.vdb.get_datasets_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

    def get_variants_db(self):
        if self.vdb is None:
            self.reload_dataset()
            assert self.vdb is not None

        return self.vdb

    def get_dataset_facade(self):
        return self.get_variants_db().dataset_facade

    def get_common_report_facade(self):
        return self.get_variants_db().common_report_facade

    def get_score_loader(self):
        return self.get_variants_db().score_loader

    def get_weights_loader(self):
        return self.get_variants_db().weights_loader


_studies_manager = None


def get_studies_manager():
    global _studies_manager
    if _studies_manager is None:
        _studies_manager = StudiesManager()
    return _studies_manager
