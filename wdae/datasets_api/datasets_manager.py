from __future__ import unicode_literals
from builtins import object

from configurable_entities.configuration import DAEConfig

from studies.factory import VariantsDb

from datasets_api.models import Dataset


__all__ = ['get_datasets_manager']


class DatasetsManager(object):

    def __init__(self, dae_config=None):
        if dae_config is None:
            dae_config = DAEConfig()
        self.dae_config = dae_config
        self.vdb = None

    def reload_dataset(self):
        self.vdb = VariantsDb(self.dae_config)

        for dataset_id in self.vdb.get_datasets_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

    def get_dataset_facade(self):
        if self.vdb is None:
            self.reload_dataset()
            assert self.vdb is not None

        return self.vdb.dataset_facade

    def get_variants_db(self):
        if self.vdb is None:
            self.reload_dataset()
            assert self.vdb is not None

        return self.vdb


_datasets_manager = None


def get_datasets_manager():
    global _datasets_manager
    if _datasets_manager is None:
        _datasets_manager = DatasetsManager()
    return _datasets_manager
