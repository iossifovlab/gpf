import abc

from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from datasets.dataset_config import DatasetConfig


class DatasetsDefinition(ConfigurableEntityDefinition):
    __metaclass__ = abc.ABCMeta

    @property
    def dataset_ids(self):
        return self.configurable_entity_ids()

    def get_dataset_config(self, dataset_id):
        return self.get_configurable_entity_config(dataset_id)

    def get_all_dataset_configs(self):
        return self.get_all_configurable_entity_configs()


class DirectoryEnabledDatasetsDefinition(DatasetsDefinition):

    ENABLED_DIR = 'datasets-enabled'

    def __init__(self, datasets_dir=None):
        super(DirectoryEnabledDatasetsDefinition, self).__init__()
        if datasets_dir is None:
            from default_settings import DATA_DATASETS_DIR
            datasets_dir = DATA_DATASETS_DIR

        self.directory_enabled_configurable_entity_definition(
            datasets_dir, DatasetConfig, 'dataset_id')


class SingleFileDatasetsDefinition(DatasetsDefinition):

    def __init__(self, config_path, work_dir=None):
        super(SingleFileDatasetsDefinition, self).__init__()
        self.single_file_configurable_entity_definition(
            config_path, work_dir, DatasetConfig, 'dataset_id')
