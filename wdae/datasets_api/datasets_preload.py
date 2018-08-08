'''
Created on Feb 17, 2017

@author: lubo
'''
from django.conf import settings

from datasets.dataset import DatasetWrapper
from datasets.datasets_definition import DirectoryEnabledDatasetsDefinition
from preloaded.register import Preload
from datasets.dataset_factory import DatasetFactory
from datasets.dataset_config import DatasetConfig
from models import Dataset
from django.db.utils import OperationalError, ProgrammingError
from precompute.register import Precompute
import logging

from studies.study_definition import StudyDefinition

logger = logging.getLogger(__name__)

logger.info("HELLO")


class DatasetsPreload(Preload, Precompute):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        self.dataset_definition = DirectoryEnabledDatasetsDefinition()
        self.studies_definition = StudyDefinition.from_environment()
        self.factory = DatasetFactory(
            _class=DatasetWrapper, studies_definition=self.studies_definition)

    def precompute(self):
        try:
            for ds in self.dataset_definition.get_all_dataset_configs():
                Dataset.recreate_dataset_perm(ds.dataset_id)
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

    def get_definitions(self):
        return self.dataset_definition


