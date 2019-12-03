import os
import copy

from box import Box

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
        # 'file_format',
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


class FilesConfigParser(ConfigParserBase):

    SECTION = 'files'
    INCLUDE_PROPERTIES = (
        '*.path',
        '*.format',
        '*.params',
    )

    @staticmethod
    def _split_type_values_dict(type_values_dict):
        if type_values_dict is None:
            return None

        type_values_dict = [tv.split(':') for tv in type_values_dict]
        res = {ft.strip(): fn.strip() for (ft, fn) in type_values_dict}
        return Box(
            res, camel_killer_box=True,
            default_box=True, default_box_attr=None)

    @classmethod
    def parse(cls, config):
        config = super(FilesConfigParser, cls).parse(config)
        if config is None:
            return None

        if not config or not config.get(cls.SECTION, None):
            return None

        config_section = copy.deepcopy(config[cls.SECTION])
        del config[cls.SECTION]

        pedigree = []
        denovo = []
        vcf = []
        for key, file_config in config_section.items():
            if file_config.params:
                file_config.params = cls._split_type_values_dict(
                    [p.strip() for p in file_config.params.split(',')]
                )
            if file_config.format == 'pedigree':
                pedigree.append(file_config)
            elif file_config.format == 'vcf':
                vcf.append(file_config)
            elif file_config.format == 'denovo':
                denovo.append(file_config)
            else:
                assert False, file_config

        assert len(pedigree) == 1

        config_section = Box({
            'pedigree': pedigree[0],
            'vcf': vcf,
            'denovo': denovo
        }, default_box=True)

        return config_section


class TablesConfigParser(ConfigParserBase):

    SECTION = 'tables'
    INCLUDE_PROPERTIES = (
        'pedigree',
        'variant',
    )

    @classmethod
    def parse(cls, config):
        config = super(TablesConfigParser, cls).parse(config)
        if config is None:
            return None

        if not config or not config.get(cls.SECTION, None):
            return None

        config_section = copy.deepcopy(config[cls.SECTION])
        del config[cls.SECTION]

        return config_section


class StudyConfigParser(StudyConfigParserBase):

    SECTION = 'study'

    INCLUDE_PROPERTIES = StudyConfigParserBase.INCLUDE_PROPERTIES + (
        'work_dir',
        'wd',
        'genotype_storage',
        'files',
        'tables',
    )

    @classmethod
    def read_and_parse_directory_configurations(
            cls, configurations_dir, defaults=None, fail_silently=False):
        print("parsing studies directory:", configurations_dir)
        configs = super(StudyConfigParser, cls). \
            read_and_parse_directory_configurations(
                configurations_dir, defaults=defaults,
                fail_silently=fail_silently
            )

        return {c.id: c for c in configs}

    @classmethod
    def _fill_files_config(cls, config_section, config):
        files_config = FilesConfigParser.parse(config)
        if not files_config:
            return

        config_section.files = files_config

    @classmethod
    def _fill_tables_config(cls, config_section, config):
        tables_config = TablesConfigParser.parse(config)
        if not tables_config:
            return

        config_section.tables = tables_config

    @classmethod
    def _fill_sections_config(cls, config_section, config):
        super(StudyConfigParser, cls)._fill_sections_config(
            config_section, config)

        cls._fill_files_config(config_section, config)
        cls._fill_tables_config(config_section, config)

        config = copy.deepcopy(config)
        del config[cls.SECTION]
        config_section.study_config = config

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
