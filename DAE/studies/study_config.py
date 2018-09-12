import os

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig
from studies.study_factory import StudyFactory


class StudyConfig(ConfigurableEntityConfig):

    SPLIT_STR_SETS = (
        'phenotypes',
    )
    CAST_TO_BOOL = (
        'hasComplex', 'hasCNV', 'hasDenovo', 'hasTransmitted',
    )

    def __init__(self, config, *args, **kwargs):
        super(StudyConfig, self).__init__(config, *args, **kwargs)
        assert 'prefix' in self
        assert self.study_name
        assert self.type
        assert self.type in StudyFactory.STUDY_TYPES.keys()
        assert self.work_dir
        assert self.phenotypes
        assert 'studyType' in self
        assert 'hasComplex' in self
        assert 'hasCNV' in self
        assert 'hasDenovo' in self
        assert 'hasTransmitted' in self
        self.make_vcf_prefix_absolute_path()

    @classmethod
    def from_config(cls, config_section, section):
        if 'enabled' in config_section:
            if config_section['enabled'] == 'false':
                return None

        cls.add_default_config_key_from_section(config_section, section,
                                                'study_name')

        return StudyConfig(config_section)

    def make_vcf_prefix_absolute_path(self):
        if not os.path.isabs(self.prefix):
            self.prefix = os.path.abspath(
                os.path.join(self.work_dir, self.study_name, self.prefix))

    @staticmethod
    def get_default_values():
        return {
            'studyType': None,
            'hasComplex': 'no',
            'hasCNV': 'no',
            'hasDenovo': 'no',
            'hasTransmitted': 'no'
        }
