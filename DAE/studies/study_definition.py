import abc

from studies.study_config import StudyConfig


class StudyDefinition(object):
    __metaclass__ = abc.ABCMeta

    configs = {}

    @property
    def study_ids(self):
        return list(self.configs.keys())

    def get_study_config(self, study_id):
        if study_id not in self.configs:
            return None

        return self.configs[study_id]

    def get_all_study_configs(self):
        return list(self.configs.values())

    def get_all_study_names(self):
        return list(self.configs.keys())

    @classmethod
    def from_environment(cls):
        work_dir = StudyDefinition._work_dir_from_environment()
        config_file = StudyDefinition._config_file_from_environment()

        return StudyDefinition.from_config_file(config_file, work_dir)

    @classmethod
    def from_config_file(cls, config_file=None, work_dir=None):
        if work_dir is None:
            work_dir = StudyDefinition._work_dir_from_environment()

        print("from_config_file", work_dir, config_file)

        return cls.from_config(StudyConfig
                               .list_from_config(config_file, work_dir))

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
