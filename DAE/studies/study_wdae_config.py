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
    def _get_present_in_role(
            cls, present_in_role_type, present_in_role_options, study_config):
        present_in_role = {}

        present_in_role['name'] = \
            study_config.pop(present_in_role_type + '.name', None)
        present_in_role['roles'] = \
            [el.strip() for el in study_config.pop(
                present_in_role_type + '.roles').split(',')]

        return present_in_role

    @classmethod
    def _get_selectors(cls, dataset_config, selector_key, selector_getter):
        selector = {}
        for key, value in dataset_config.items():
            option_type, option_fullname = cls._split_section(key)
            if option_type != selector_key:
                continue

            selector_type, selector_option =\
                cls._split_section(option_fullname)
            if selector_key + '.' + selector_type not in selector:
                selector[selector_key + '.' + selector_type] =\
                    [selector_option]
            else:
                selector[selector_key + '.' + selector_type].append(
                    selector_option)

        selectors = []
        for selector_type, selector_options in selector.items():
            selectors.append(selector_getter(
                selector_type, selector_options, dataset_config))

        return selectors

    @classmethod
    def _fill_wdae_people_group_config(cls, config_section):
        people_group = cls._get_selectors(
            config_section, 'peopleGroup', cls._get_pedigree)
        if people_group:
            config_section['pedigreeSelectors'] = people_group
            config_section['peopleGroup'] = config_section['pedigreeSelectors']

    @classmethod
    def _fill_wdae_present_in_role_config(cls, config_section):
        present_in_role = cls._get_selectors(
            config_section, 'presentInRole', cls._get_present_in_role)
        if present_in_role:
            config_section['presentInRole'] = present_in_role

    @classmethod
    def _fill_wdae_enrichment_tool_config(cls, config_section):
        config_section = cls._combine_dict_options(
            config_section,
            dict_options_keys=['enrichmentTool'])

    @classmethod
    def _fill_wdae_config(cls, config_section):
        cls._fill_wdae_people_group_config(config_section)
        cls._fill_wdae_present_in_role_config(config_section)
        cls._fill_wdae_enrichment_tool_config(config_section)
