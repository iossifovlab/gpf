import abc

from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from studies.dataset_config import DatasetConfig


class DatasetsDefinition(ConfigurableEntityDefinition):
    __metaclass__ = abc.ABCMeta

    @property
    def dataset_ids(self):
        return self.configurable_entity_ids()

    def get_dataset_config(self, dataset_id):
        return self.get_configurable_entity_config(dataset_id)

    def get_all_dataset_configs(self):
        return self.get_all_configurable_entity_configs()

    @staticmethod
    def get_skip_sections():
        return ['commonReport']


class DirectoryEnabledDatasetsDefinition(DatasetsDefinition):

    ENABLED_DIR = '.'

    def __init__(self, study_facade, datasets_dir, work_dir):
        super(DirectoryEnabledDatasetsDefinition, self).__init__()
        assert datasets_dir is not None
        assert work_dir is not None
        self.study_facade = study_facade

        self.directory_enabled_configurable_entity_definition(
            datasets_dir, DatasetConfig, work_dir, 'id',
            DatasetConfig.get_default_values(work_dir),
            DatasetsDefinition.get_skip_sections())
        self._fill_studies_configs()

    def _fill_studies_configs(self):
        for dataset_config in self.configs.values():
            studies_configs = []
            for study_id in dataset_config.studies:
                study_config = self.study_facade.get_study_config(study_id)
                studies_configs.append(study_config)
            dataset_config.studies_configs = studies_configs


# class SingleFileDatasetsDefinition(DatasetsDefinition):

#     def __init__(self, config_path, work_dir=None):
#         super(SingleFileDatasetsDefinition, self).__init__()
#         if work_dir is None:
#             work_dir = DatasetsDefinition._work_dir_from_environment()

#         self.single_file_configurable_entity_definition(
#             config_path, work_dir, DatasetConfig, 'dataset_id',
#             DatasetConfig.get_default_values(),
#             DatasetsDefinition.get_skip_sections())
