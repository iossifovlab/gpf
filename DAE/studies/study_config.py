import os

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
        assert self.phenotypes
        self.make_vcf_prefix_absolute_path()

    @classmethod
    def from_config(cls, config_section, section):
        if 'enabled' in config_section:
            if config_section['enabled'] == 'false':
                return None

        cls.add_default_config_key_from_section(config_section, section,
                                                'study_name')

        if 'phenotypes' in config_section:
            config_section['phenotypes'] = set(
                config_section['phenotypes'].split(','))

        return StudyConfig(config_section)

    def make_vcf_prefix_absolute_path(self):
        if not os.path.isabs(self.prefix):
            self.prefix = os.path.abspath(
                os.path.join(self.work_dir, self.study_name, self.prefix))

