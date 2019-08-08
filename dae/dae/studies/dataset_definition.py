import abc

from dae.configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from dae.studies.dataset_config import DatasetConfig


class DatasetsDefinition(ConfigurableEntityDefinition):
    __metaclass__ = abc.ABCMeta

    @property
    def dataset_ids(self):
        return self.configurable_entity_ids

    def get_dataset_config(self, dataset_id):
        return self.get_configurable_entity_config(dataset_id)

    def get_all_dataset_configs(self):
        return self.get_all_configurable_entity_configs()


class DirectoryEnabledDatasetsDefinition(DatasetsDefinition):

    ENABLED_DIR = '.'

    def __init__(
            self, study_facade, datasets_dir, work_dir, default_conf=None):
        super(DirectoryEnabledDatasetsDefinition, self).__init__()
        assert datasets_dir is not None
        assert work_dir is not None
        self.study_facade = study_facade

        self.directory_enabled_configurable_entity_definition(
            datasets_dir, DatasetConfig, work_dir, default_conf=default_conf,
            fail_silently=True)
        self._fill_studies_configs()

    def _fill_studies_configs(self):
        for dataset_config in self.configs.values():
            studies_configs = []
            for study_id in dataset_config.studies:
                study_config = self.study_facade.get_study_config(study_id)
                studies_configs.append(study_config)
            dataset_config.studies_configs = studies_configs
