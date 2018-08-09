import os
import reusables

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig
from studies.study_factory import StudyFactory


class StudyConfig(ConfigurableEntityConfig):

    def __init__(self, *args, **kwargs):
        super(StudyConfig, self).__init__(*args, **kwargs)
        assert self.prefix
        assert self.study_name
        assert self.type
        assert self.type in StudyFactory.STUDY_TYPES.keys()
        assert self.work_dir
        self.make_vcf_prefix_absolute_path()

    @classmethod
    def list_from_config(cls, config_file=None, work_dir=None):
        if config_file is None:
            config_file = cls._config_file_from_environment()

        config = cls.get_config(
            config_file, work_dir, cls._default_settings_from_environment(),
            'work_dir')

        result = list()
        for section in config.keys():
            if 'enabled' in config[section]:
                if config[section]['enabled'] == 'false':
                    continue
            cls.add_default_study_name_from_section(config, section)

            result.append(StudyConfig(config[section]))

        return result

    @classmethod
    def add_default_study_name_from_section(cls, config, section):
        if 'study_name' not in config[section]:
            config[section]['study_name'] = section

    def make_vcf_prefix_absolute_path(self):
        if not os.path.isabs(self.prefix):
            self.prefix = os.path.abspath(
                os.path.join(self.work_dir, self.study_name, self.prefix))

    @staticmethod
    def _default_settings_from_environment():
        from studies import default_settings
        return default_settings

    @staticmethod
    def _config_file_from_environment():
        from studies.default_settings import CONFIG_FILE
        return CONFIG_FILE
