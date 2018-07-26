import abc

from studies.study_config import StudyConfig


class StudyDefinition(object):
    __metaclass__ = abc.ABCMeta

    configs = {}

    @property
    def dataset_ids(self):
        return list(self.configs.keys())

    def get_dataset_config(self, dataset_id):
        if dataset_id not in self.configs:
            return None

        return self.configs[dataset_id]

    def get_all_dataset_configs(self):
        return list(self.configs.values())

    @classmethod
    def from_config_file(cls, config_file):
        return cls.from_config(StudyConfig.list_from_config(config_file))

    @staticmethod
    def from_config(configs):
        definition = StudyDefinition()

        definition.configs = {
            config.study_name: config
            for config in configs
        }

        return definition
