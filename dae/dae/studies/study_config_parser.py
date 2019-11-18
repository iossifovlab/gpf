import os
import copy

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

    INCLUDE_PROPERTIES = (
        'name',
        'id',
        'description',
        'prefix',
        'file_format',
        'phenoDB',
        'studyType',
        'year',
        'pubMed',
        'hasDenovo',
        'hasTransmitted',
        'hasComplex',
        'hasCNV',
        'commonReport',
        'genotypeBrowser',
        'phenotypeBrowser',
        'enrichmentTool',
        'phenotypeTool',
        'enabled',
    )

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

        if os.path.exists(config_section.description):
            with open(config_section.description) as desc:
                config_section.description = desc.read()

        return config_section

    @classmethod
    def _fill_people_group_config(cls, config_section, config):
        people_group_config = PeopleGroupConfigParser.parse(config)

        if people_group_config and people_group_config.people_group:
            config_section.peopleGroupConfig = people_group_config

    @classmethod
    def _fill_genotype_browser_config(cls, config_section, config):
        genotype_browser_config = GenotypeBrowserConfigParser.parse(config)

        if genotype_browser_config and config_section.genotype_browser:
            config_section.genotypeBrowserConfig = genotype_browser_config

    @classmethod
    def _fill_sections_config(cls, config_section, config):
        cls._fill_people_group_config(config_section, config)
        cls._fill_genotype_browser_config(config_section, config)
        config = copy.deepcopy(config)
        del config[cls.SECTION]
        config_section.study_config = config


class StudyConfigParser(StudyConfigParserBase):

    SECTION = 'study'

    INCLUDE_PROPERTIES = StudyConfigParserBase.INCLUDE_PROPERTIES + (
        'work_dir',
        'genotype_storage'
    )

    @classmethod
    def read_and_parse_directory_configurations(
            cls, configurations_dir, defaults=None, fail_silently=False):
        configs = super(StudyConfigParser, cls). \
            read_and_parse_directory_configurations(
                configurations_dir, defaults=defaults,
                fail_silently=fail_silently
            )

        return {c.id: c for c in configs}

    @classmethod
    def parse(cls, config):
        config = super(StudyConfigParser, cls).parse(config)
        if config is None:
            return None

        config.years = [config.year] if config.year else []
        config.pub_meds = [config.pub_med] if config.pub_med else []
        config.studyTypes = \
            {config.study_type} if config.get('studyType', None) else set()

        assert config.name
        assert config.genotype_storage
        assert config.work_dir
        assert 'studyType' in config
        assert 'hasComplex' in config
        assert 'hasCNV' in config
        assert 'hasDenovo' in config
        assert 'hasTransmitted' in config

        return config
