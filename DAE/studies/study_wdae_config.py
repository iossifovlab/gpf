from studies.people_group_config import PeopleGroupConfig
from studies.genotype_browser_config import GenotypeBrowserConfig


class StudyWdaeMixin(object):

    @classmethod
    def _fill_people_group_config(cls, config_section, config):
        people_group_config = PeopleGroupConfig.from_config(config)
        if people_group_config is not None:
            config_section['peopleGroupConfig'] = people_group_config

    @classmethod
    def _fill_genotype_browser_config(cls, config_section, config):
        genotype_browser_config = GenotypeBrowserConfig.from_config(config)
        if genotype_browser_config is not None and \
                config_section.get('genotypeBrowser', False) is True:
            config_section['genotypeBrowserConfig'] = genotype_browser_config

    @classmethod
    def _fill_wdae_config(cls, config_section, config):
        cls._fill_people_group_config(config_section, config)
        cls._fill_genotype_browser_config(config_section, config)

        config_section['studyConfig'] = config
