'''
Created on Feb 17, 2017

@author: lubo
'''
from django.conf import settings

from datasets.dataset_facade import DatasetFacade
from preloaded.register import Preload
from datasets_api.models import Dataset
from django.db.utils import OperationalError, ProgrammingError
from precompute.register import Precompute
import logging


logger = logging.getLogger(__name__)


class DatasetsPreload(Preload, Precompute):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        self.dataset_facade = DatasetFacade()

    def precompute(self):
        try:
            for dataset_id in self.dataset_facade.get_all_dataset_ids():
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
            for dataset_id in self.dataset_facade.load_cache():
                logger.info(dataset_id)

    def get(self):
        return self

    def get_facade(self):
        return self.dataset_facade

    def get_definition(self):
        return self.dataset_facade.get_dataset_definition()

    def get_factory(self):
        return self.dataset_facade.get_dataset_factory()
