import abc

from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from study_groups.study_group_config import StudyGroupConfig


class StudyGroupsDefinition(ConfigurableEntityDefinition):
    __metaclass__ = abc.ABCMeta

    @property
    def study_group_ids(self):
        return self.configurable_entity_ids()

    def get_study_group_config(self, study_group_id):
        return self.get_configurable_entity_config(study_group_id)

    def get_all_study_group_configs(self):
        return self.get_all_configurable_entity_configs()


class SingleFileStudiesGroupDefinition(StudyGroupsDefinition):

    def __init__(self, config_path, work_dir=None):
        super(SingleFileStudiesGroupDefinition, self).__init__()
        if work_dir is None:
            work_dir = SingleFileStudiesGroupDefinition. \
                _work_dir_from_environment()
        if config_path is None:
            config_path = SingleFileStudiesGroupDefinition. \
                _config_file_from_environment()

        self.single_file_configurable_entity_definition(
            config_path, work_dir, StudyGroupConfig, 'name')

    @staticmethod
    def _config_file_from_environment():
        from study_groups.default_settings import CONFIG_FILE
        return CONFIG_FILE

    @staticmethod
    def _work_dir_from_environment():
        from study_groups.default_settings import DATA_DIR
        return DATA_DIR
