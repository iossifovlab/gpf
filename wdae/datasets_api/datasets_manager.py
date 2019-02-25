from __future__ import unicode_literals
from builtins import object
import os

from configurable_entities.configuration import DAEConfig

from studies.factory import VariantsDb

from datasets_api.models import Dataset


__all__ = ['get_datasets_manager']


class DatasetsManager(object):

    def __init__(self, dae_config=None):
        if dae_config is None:
            dae_config = DAEConfig()
        self.dae_config = dae_config
        self.vdb = VariantsDb(self.dae_config)
        self.facade = None

    def reload_dataset(self):
        self.facade = self.vdb.dataset_facade

        for dataset_id in self.facade.get_all_dataset_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

    def get_dataset_facade(self):
        if self.facade is None:
            self.reload_dataset()
            assert self.facade is not None

        return self.facade


_datasets_manager = None


def get_datasets_manager():
    global _datasets_manager
    if _datasets_manager is None:
        _datasets_manager = DatasetsManager()
    return _datasets_manager
