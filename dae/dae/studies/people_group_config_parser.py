from dae.configuration.dae_config_parser import ConfigParserBase


class PeopleGroupConfigParser(ConfigParserBase):

    SECTION = 'peopleGroup'

    SPLIT_STR_LISTS = [
        'selectedPeopleGroupValues'
    ]

    @staticmethod
    def _people_group_selectors_split_dict(dict_to_split):
        options = dict_to_split.split(':')
        return {'id': options[0], 'name': options[1], 'color': options[2]}

    @classmethod
    def _split_dict_lists(cls, dict_to_split):
        options = [cls._people_group_selectors_split_dict(el.strip())
                   for el in dict_to_split.split(',')]
        return options

    @staticmethod
    def _get_values(options):
        return {option['id']: option for option in options}

    @classmethod
    def _get_people_groups(cls, config):
        selected_people_groups = config.selected_people_group_values
        people_groups = []

        for people_group_id, people_group in config.items():
            if not isinstance(people_group, dict):
                continue
            if selected_people_groups and \
                    people_group_id not in selected_people_groups:
                continue

            people_group['id'] = people_group_id

            people_group['default'] = cls._people_group_selectors_split_dict(
                people_group['default'])
            people_group['domain'] = cls._split_dict_lists(
                people_group['domain'])
            people_group['values'] = cls._get_values(people_group['domain'])

            people_groups.append(people_group)

        return people_groups

    @staticmethod
    def _get_description_keys():
        return [
            'peopleGroup'
        ]

    @classmethod
    def get_config_description(cls, config):
        keys = cls._get_description_keys()
        config = config.to_dict()

        result = {key: config.get(key, None) for key in keys}

        return result

    @classmethod
    def parse(cls, config):
        config = super(PeopleGroupConfigParser, cls).parse(config)
        config[cls.SECTION]['peopleGroup'] = \
            cls._get_people_groups(config[cls.SECTION])

        return config
