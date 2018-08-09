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
        return cls.return_single_file_configurable_entity_definition(
            config_file, work_dir, StudyConfig, StudyDefinition, 'study_name')
