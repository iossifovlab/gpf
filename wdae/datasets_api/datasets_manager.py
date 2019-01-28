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

    def reload_dataset_facade(self):
        work_dir = os.environ.get("DAE_DB_DIR")
        config_file = os.environ.get("DAE_DATA_DIR")
        study_definition = DirectoryEnabledStudiesDefinition(
            os.path.join(config_file, 'studies'), work_dir)
        study_facade = StudyFacade(study_definition)

        dataset_definitions = DirectoryEnabledDatasetsDefinition(
            study_facade, os.path.join(config_file, 'datasets'), work_dir)
        dataset_factory = DatasetFactory(study_facade)

        self.facade =\
            DatasetFacade(dataset_definitions, dataset_factory)
        # self.facade = DatasetFacade(
        #     dataset_definition=self.dataset_definition,
        #     dataset_factory=self.dataset_factory)

        for dataset_id in self.facade.get_all_dataset_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

    def get_dataset_facade(self):
        if self.facade is None:
            self.reload_dataset_facade()
            assert self.facade is not None

        return self.facade


datasets_manager = DatasetsManager()


def get_datasets_manager():
    return datasets_manager
