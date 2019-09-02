from dae.studies.people_group_config_parser import PeopleGroupConfigParser
from dae.studies.genotype_browser_config_parser import \
    GenotypeBrowserConfigParser


class StudySectionsConfigMixin(object):

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
