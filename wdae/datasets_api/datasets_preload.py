'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from preloaded.register import Preload
from precompute.register import Precompute

from datasets_api.models import Dataset
from datasets_api.datasets_manager import get_datasets_manager


logger = logging.getLogger(__name__)


class DatasetsPreload(Preload, Precompute):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        datasets_facade = get_datasets_manager().get_dataset_facade()
        self._dataset_facade = datasets_facade

    def precompute(self):
        try:
            for dataset_id in self._dataset_facade.get_all_dataset_ids():
                Dataset.recreate_dataset_perm(dataset_id)
        except (OperationalError, ProgrammingError):
            # Database migrations are probably not run yet, ignore exception
            pass

    def serialize(self):
        return {}

    def deserialize(self, data):
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
            for dataset_id in self._dataset_facade.load_cache():
                logger.info(dataset_id)
                # self.factory.get_dataset(dataset_id)

    def get(self):
        return self

    def get_facade(self):
        return self._dataset_facade
