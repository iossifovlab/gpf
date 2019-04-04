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
    def _fill_wdae_enrichment_tool_config(cls, config_section):
        config_section = cls._combine_dict_options(
            config_section,
            dict_options_keys=['enrichmentTool'])

    @classmethod
    def _fill_wdae_config(cls, config_section):
        cls._fill_wdae_enrichment_tool_config(config_section)
