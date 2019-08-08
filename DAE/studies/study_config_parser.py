import os

from studies.study_wdae_config import StudyWdaeMixin
from configuration.dae_config_parser import DAEConfigParser


class StudyConfigParserBase(DAEConfigParser, StudyWdaeMixin):

    SPLIT_STR_SETS = (
        'phenotypes',
    )

    CAST_TO_BOOL = (
        'hasComplex',
        'hasCNV',
        'hasDenovo',
        'hasTransmitted',
        'phenotypeBrowser',
        'phenotypeTool',
        'enrichmentTool',
        'genotypeBrowser',
        'commonReport'
    )

    SPLIT_STR_LISTS = [
        'authorizedGroups'
    ]

    @classmethod
    def parse(cls, config):
        config = super(StudyConfigParserBase, cls).parse(config)
        if config is None:
            return None

        config_section = config[cls.SECTION]
        cls._fill_wdae_config(config_section, config)

        assert config_section.id

        if config_section.get('name') is None:
            config_section.name = config_section.id

        assert config_section.name
        assert 'description' in config_section
        assert config_section.work_dir

        return config_section


class StudyConfigParser(StudyConfigParserBase):

    SECTION = 'study'

    @classmethod
    def parse(cls, config):
        config = super(StudyConfigParser, cls).parse(config)
        if config is None:
            return None

        cls.make_prefix_absolute_path(config)

        config.authorizedGroups = config.get(
            'authorizedGroups', [config.get('id', '')])

        assert config.name
        assert config.prefix
        # assert config.pedigree_file
        assert config.file_format
        assert config.work_dir
        # assert config.phenotypes
        assert 'studyType' in config
        assert 'hasComplex' in config
        assert 'hasCNV' in config
        assert 'hasDenovo' in config
        assert 'hasTransmitted' in config

        return config

    @staticmethod
    def make_prefix_absolute_path(config):
        if not os.path.isabs(config.prefix):
            config_filename = config.study_config.config_file
            dirname = os.path.dirname(config_filename)
            config.prefix = os.path.abspath(
                os.path.join(dirname, config.prefix))
