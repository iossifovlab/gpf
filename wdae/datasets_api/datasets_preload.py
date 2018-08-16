'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf import settings

from datasets.dataset import DatasetWrapper
from datasets.datasets_definition import DirectoryEnabledDatasetsDefinition
from preloaded.register import Preload
from datasets.dataset_factory import DatasetFactory
from datasets.dataset_config import DatasetConfig
from datasets_api.models import Dataset
from django.db.utils import OperationalError, ProgrammingError
from precompute.register import Precompute
import logging

logger = logging.getLogger(__name__)


class DatasetsPreload(Preload, Precompute):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        # self.dataset_config = DatasetConfig()
        self.dataset_definition = DirectoryEnabledDatasetsDefinition()
        self.factory = DatasetFactory(
            self.dataset_definition, _class=DatasetWrapper)

    def precompute(self):
        try:
            for ds in self.dataset_definition.get_datasets():
                Dataset.recreate_dataset_perm(ds['id'])
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
        logger.warn("PRELOAD_ACTIVE is {}".format(preload_active))
        if preload_active:
            for dset in self.dataset_definition.get_all_dataset_configs():
                dataset_id = dset.dataset_id
                logger.info(dataset_id)
                self.factory.get_dataset(dataset_id)

    def get(self):
        return self

    def get_factory(self):
        return self.factory

    def get_config(self):
        return self.dataset_definition
