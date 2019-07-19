from studies.people_group_config import PeopleGroupConfig
from studies.genotype_browser_config import GenotypeBrowserConfig


class StudyWdaeMixin(object):

    @staticmethod
    def _combine_dict_options(
            dataset_config, dict_options_keys=['enrichmentTool']):

        for key in dict_options_keys:
            if dataset_config.get(key, True):
                dict_options = {}
                keys_to_remove = []
                for k in dataset_config.keys():
                    if k.startswith(key + '.'):
                        keys_to_remove.append(k)
                        dict_options[k.replace(key + '.', '')] =\
                            dataset_config.get(k)
                for k in keys_to_remove:
                    dataset_config.pop(k)
                if dict_options:
                    dataset_config[key] = dict_options

        return dataset_config

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
    def _fill_wdae_enrichment_tool_config(cls, config_section):
        config_section = cls._combine_dict_options(
            config_section,
            dict_options_keys=['enrichmentTool'])

    @classmethod
    def _fill_wdae_config(cls, config_section, config):
        cls._fill_people_group_config(config_section, config)
        cls._fill_genotype_browser_config(config_section, config)
        cls._fill_wdae_enrichment_tool_config(config_section)

        config_section['studyConfig'] = config
