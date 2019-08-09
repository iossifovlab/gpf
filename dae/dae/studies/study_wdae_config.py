from dae.studies.people_group_config import PeopleGroupConfig
from dae.studies.genotype_browser_config import GenotypeBrowserConfig


class StudyWdaeMixin(object):

    @classmethod
    def _fill_people_group_config(cls, config_section, config):
        if PeopleGroupConfig.SECTION not in config:
            return None
        people_group_config = PeopleGroupConfig.parse(config)
        if people_group_config is not None and \
                PeopleGroupConfig.SECTION in people_group_config:
            people_group_config = \
                people_group_config[PeopleGroupConfig.SECTION]
            if 'peopleGroup' in people_group_config:
                config_section['peopleGroupConfig'] = people_group_config

    @classmethod
    def _fill_genotype_browser_config(cls, config_section, config):
        if GenotypeBrowserConfig.SECTION not in config:
            return None
        genotype_browser_config = GenotypeBrowserConfig.parse(config)
        if genotype_browser_config is not None and \
                config_section.get('genotypeBrowser', False) is True:
            config_section['genotypeBrowserConfig'] = genotype_browser_config

    @classmethod
    def _fill_wdae_config(cls, config_section, config):
        cls._fill_people_group_config(config_section, config)
        cls._fill_genotype_browser_config(config_section, config)

        config_section['studyConfig'] = config
