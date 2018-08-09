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
    def from_environment(cls):
        work_dir = StudyDefinition._work_dir_from_environment()
        config_file = StudyDefinition._config_file_from_environment()

        return cls.multiple_files_configurable_entity_definition(
            config_file, work_dir)

    @classmethod
    def from_config_file(cls, config_file=None, work_dir=None):
        print("from_config_file", work_dir, config_file)

        return cls.multiple_files_configurable_entity_definition(
            StudyConfig.list_from_config(config_file, work_dir))

    @staticmethod
    def from_config(configs):
        definition = StudyDefinition()

        definition.configs = {
            config.study_name: config
            for config in configs
        }

        return definition

    @staticmethod
    def _work_dir_from_environment():
        from studies.default_settings import DATA_DIR
        return DATA_DIR

    @staticmethod
    def _config_file_from_environment():
        from studies.default_settings import CONFIG_FILE
        return CONFIG_FILE
