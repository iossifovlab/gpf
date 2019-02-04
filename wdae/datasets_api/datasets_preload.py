'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf import settings
import os

from studies.dataset_facade import DatasetFacade
from studies.dataset_factory import DatasetFactory
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.study_facade import StudyFacade
from studies.study_definition import DirectoryEnabledStudiesDefinition
from preloaded.register import Preload
from datasets_api.models import Dataset
from django.db.utils import OperationalError, ProgrammingError
from precompute.register import Precompute
import logging


logger = logging.getLogger(__name__)


class DatasetsPreload(Preload, Precompute):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        work_dir = os.environ.get("DAE_DB_DIR")
        config_file = os.environ.get("DAE_DATA_DIR")
        study_definition = DirectoryEnabledStudiesDefinition(
            os.path.join(config_file, 'studies'), work_dir)
        study_facade = StudyFacade(study_definition)

        dataset_definitions = DirectoryEnabledDatasetsDefinition(
            study_facade, os.path.join(config_file, 'datasets'), work_dir)
        dataset_factory = DatasetFactory(study_facade)
        self._dataset_facade =\
            DatasetFacade(dataset_definitions, dataset_factory)

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
