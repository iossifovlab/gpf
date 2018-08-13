import abc

from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from studies.study_config import StudyConfig


class StudyDefinition(ConfigurableEntityDefinition):
    __metaclass__ = abc.ABCMeta

    @property
    def study_ids(self):
        return self.configurable_entity_ids()

    def get_study_config(self, study_id):
        return self.get_configurable_entity_config(study_id)

    def get_all_study_configs(self):
        return self.get_all_configurable_entity_configs()

    def get_all_study_names(self):
        return self.get_all_configurable_entity_names()

    @classmethod
    def from_single_file(cls, config_file=None, work_dir=None):
        if work_dir is None:
            work_dir = cls._work_dir_from_environment()
        if config_file is None:
            config_file = cls._config_file_from_environment()

        return cls.get_definition_from_config(
            config_file, work_dir, StudyConfig, StudyDefinition, 'study_name')

    @staticmethod
    def _work_dir_from_environment():
        from studies.default_settings import DATA_DIR
        return DATA_DIR

    @staticmethod
    def _config_file_from_environment():
        from studies.default_settings import CONFIG_FILE
        return CONFIG_FILE
