import os

from dae.studies.people_group_config_parser import PeopleGroupConfigParser
from dae.studies.genotype_browser_config_parser import \
    GenotypeBrowserConfigParser

from dae.configuration.config_parser_base import ConfigParserBase


class StudyConfigParserBase(ConfigParserBase):

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
        cls._fill_sections_config(config_section, config)

        assert config_section.id

        if config_section.get('name') is None:
            config_section.name = config_section.id

        assert config_section.name
        assert 'description' in config_section
        assert config_section.work_dir

        return config_section

    @classmethod
    def _fill_people_group_config(cls, config_section, config):
        if PeopleGroupConfigParser.SECTION not in config:
            return None
        people_group_config = PeopleGroupConfigParser.parse(config)
        if people_group_config is not None and \
                PeopleGroupConfigParser.SECTION in people_group_config:
            people_group_config = \
                people_group_config[PeopleGroupConfigParser.SECTION]
            if 'peopleGroup' in people_group_config:
                config_section['peopleGroupConfig'] = people_group_config

    @classmethod
    def _fill_genotype_browser_config(cls, config_section, config):
        if GenotypeBrowserConfigParser.SECTION not in config:
            return None
        genotype_browser_config = GenotypeBrowserConfigParser.parse(config)
        if genotype_browser_config is not None and \
                config_section.get('genotypeBrowser', False) is True:
            config_section['genotypeBrowserConfig'] = genotype_browser_config

    @classmethod
    def _fill_sections_config(cls, config_section, config):
        cls._fill_people_group_config(config_section, config)
        cls._fill_genotype_browser_config(config_section, config)

        config_section['studyConfig'] = config


class StudyConfigParser(StudyConfigParserBase):

    SECTION = 'study'

    @classmethod
    def read_and_parse_directory_configurations(
            cls, configurations_dir, work_dir, defaults=None,
            fail_silently=False):
        configs = super(StudyConfigParser, cls). \
            read_and_parse_directory_configurations(
                configurations_dir, work_dir, defaults=defaults,
                fail_silently=fail_silently
            )

        return {c.id: c for c in configs}

    @classmethod
    def parse(cls, config):
        config = super(StudyConfigParser, cls).parse(config)
        if config is None:
            return None

        cls.make_prefix_absolute_path(config)

        config.authorizedGroups = config.get(
            'authorizedGroups', [config.get('id', '')])

        config.years = [config.year] if config.year else []
        config.pub_meds = [config.pub_med] if config.pub_med else []
        config.study_types = \
            {config.study_type} if config.get('studyType', None) else set()

        assert config.name
        assert config.prefix
        # assert config.pedigree_file
        assert config.file_format
        assert config.work_dir
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
