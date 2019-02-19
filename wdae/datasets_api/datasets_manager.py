from __future__ import unicode_literals
from builtins import object
import os

# from datasets.dataset_facade import DatasetFacade
from studies.dataset_facade import DatasetFacade
from studies.dataset_factory import DatasetFactory
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.study_facade import StudyFacade
from studies.study_definition import DirectoryEnabledStudiesDefinition
from datasets_api.models import Dataset


__all__ = ['get_datasets_manager']


class DatasetsManager(object):

    def __init__(self):
        self.facade = None
        self.dataset_definition = None
        self.dataset_factory = None

    def reload_dataset(self):
        work_dir = os.environ.get("DAE_DB_DIR")
        config_file = os.environ.get("DAE_DATA_DIR")
        study_definition = DirectoryEnabledStudiesDefinition(
            os.path.join(config_file, 'studies'), work_dir)
        study_facade = StudyFacade(study_definition)

        self.dataset_definitions = DirectoryEnabledDatasetsDefinition(
            study_facade, os.path.join(config_file, 'datasets'), work_dir)
        self.dataset_factory = DatasetFactory(study_facade)

        self.facade =\
            DatasetFacade(self.dataset_definitions, self.dataset_factory)

        for dataset_id in self.facade.get_all_dataset_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

    def get_dataset_facade(self):
        if self.facade is None:
            self.reload_dataset()
            assert self.facade is not None

        return self.facade

    def get_dataset_factory(self):
        if self.dataset_factory is None:
            self.reload_dataset()
            assert self.dataset_factory is not None

        return self.dataset_factory


_datasets_manager = None


def get_datasets_manager():
    global _datasets_manager
    if _datasets_manager is None:
        _datasets_manager = DatasetsManager()
    return _datasets_manager
