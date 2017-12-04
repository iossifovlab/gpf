'''
Created on Feb 17, 2017

@author: lubo
'''
from django.conf import settings
from preloaded.register import Preload
from datasets.datasets_factory import DatasetsFactory
from datasets.config import DatasetsConfig
from models import Dataset
from django.db.utils import OperationalError, ProgrammingError
from precompute.register import Precompute


class DatasetsPreload(Preload, Precompute):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        self.dataset_config = DatasetsConfig()
        self.factory = DatasetsFactory(self.dataset_config)

    def precompute(self):
        try:
            for ds in self.dataset_config.get_datasets(True):
                Dataset.recreate_dataset_perm(ds['id'], ds['authorizedGroups'])
        except OperationalError:
            # Database migrations are probably not run yet, ignore exception
            pass
        except ProgrammingError:
            # Database migrations are probably not run yet, ignore exception
            pass

    def serialize(self):
        return {}

    def deserialize(self):
        self.load()
        return {}

    def is_precomputed(self):
        return self.is_loaded()

    def is_loaded(self):
        return True

    def load(self):
        preload_active = getattr(
            settings,
            "PRELOAD_ACTIVE",
            False)

        if preload_active:
            for dset in self.dataset_config.get_datasets():
                dataset_id = dset['id']
                self.factory.get_dataset(dataset_id)

    def get(self):
        return self

    def get_factory(self):
        return self.factory

    def get_config(self):
        return self.dataset_config
