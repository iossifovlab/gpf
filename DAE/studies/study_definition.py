from __future__ import unicode_literals

import abc

from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from studies.study_config import StudyConfig


class StudyDefinition(ConfigurableEntityDefinition):
    __metaclass__ = abc.ABCMeta

    @property
    def study_ids(self):
        return self.configurable_entity_ids

    def get_study_config(self, study_id):
        return self.get_configurable_entity_config(study_id)

    def get_all_study_configs(self):
        return self.get_all_configurable_entity_configs()

    def get_all_study_names(self):
        return self.get_all_configurable_entity_names()

    @staticmethod
    def get_skip_sections():
        return ['commonReport']


class SingleFileStudiesDefinition(StudyDefinition):

    def __init__(self, config_file=None, work_dir=None):
        super(SingleFileStudiesDefinition, self).__init__()
        assert work_dir is not None
        assert config_file is not None

        self.single_file_configurable_entity_definition(
            config_file, work_dir, StudyConfig, "study_name",
            StudyConfig.get_default_values(work_dir),
            StudyDefinition.get_skip_sections())


class DirectoryEnabledStudiesDefinition(StudyDefinition):

    ENABLED_DIR = '.'

    def __init__(self, studies_dir, work_dir):
        super(DirectoryEnabledStudiesDefinition, self).__init__()
        assert studies_dir is not None
        assert work_dir is not None

        self.directory_enabled_configurable_entity_definition(
            studies_dir, StudyConfig, work_dir, 'id',
            StudyConfig.get_default_values(work_dir),
            StudyDefinition.get_skip_sections())
