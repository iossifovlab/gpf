class StudyWdaeMixin(object):

    @staticmethod
    def _split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

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

    @staticmethod
    def _get_values(options):
        return {option['id']: option for option in options}

    @staticmethod
    def _pedigree_selectors_split_dict(dict_to_split):
        options = dict_to_split.split(':')
        return {'id': options[0], 'name': options[1], 'color': options[2]}

    @classmethod
    def _split_dict_lists(cls, dict_to_split):
        options = [cls._pedigree_selectors_split_dict(el.strip())
                   for el in dict_to_split.split(',')]
        return options

    @classmethod
    def _get_pedigree(cls, pedigree_type, pedigree_options, study_config):
        pedigree = {}

        pedigree['name'] = study_config.pop(pedigree_type + '.name', None)
        pedigree['source'] = study_config.get(pedigree_type + '.source', None)
        _, pedigree['id'] = cls._split_section(pedigree_type)
        pedigree['default'] =\
            cls._pedigree_selectors_split_dict(
                study_config.pop(pedigree_type + '.default'))
        pedigree['domain'] =\
            cls._split_dict_lists(
                study_config.pop(pedigree_type + '.domain'))
        pedigree['values'] =\
            cls._get_values(pedigree['domain'])

        return pedigree

    @classmethod
    def _get_pedigree_selectors(cls, dataset_config, pedigree_key):
        pedigree = {}
        for key, value in dataset_config.items():
            option_type, option_fullname = cls._split_section(key)
            if option_type != pedigree_key:
                continue

            pedigree_type, pedigree_option =\
                cls._split_section(option_fullname)
            if pedigree_key + '.' + pedigree_type not in pedigree:
                pedigree[pedigree_key + '.' + pedigree_type] =\
                    [pedigree_option]
            else:
                pedigree[pedigree_key + '.' + pedigree_type].append(
                    pedigree_option)

        pedigrees = []
        for pedigree_type, pedigree_options in pedigree.items():
            if 'domain' in pedigree_options:
                pedigrees.append(cls._get_pedigree(
                    pedigree_type, pedigree_options, dataset_config))

        return pedigrees

    @staticmethod
    def _get_pedigree_selector_column(
            pedigree_selector_column, dataset_config, parent_key,
            pedigree_key):

        pedigree = {}

        pedigree['id'] = pedigree_selector_column
        pedigree['name'] = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + pedigree_selector_column +
            '.name', None)
        pedigree['role'] = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + pedigree_selector_column +
            '.role', None)
        pedigree['source'] = dataset_config.get(
            pedigree_key + '.' + pedigree_selector_column + '.source', None)

        return pedigree

    @classmethod
    def _fill_wdae_people_group_config(cls, config_section):
        people_group =\
            cls._get_pedigree_selectors(config_section, 'peopleGroup')
        if people_group:
            config_section['pedigreeSelectors'] = people_group
            config_section['peopleGroup'] = config_section['pedigreeSelectors']

    @classmethod
    def _fill_wdae_enrichment_tool_config(cls, config_section):
        config_section = cls._combine_dict_options(
            config_section,
            dict_options_keys=['enrichmentTool'])

    @classmethod
    def _fill_wdae_config(cls, config_section):
        cls._fill_wdae_people_group_config(config_section)
        cls._fill_wdae_enrichment_tool_config(config_section)
