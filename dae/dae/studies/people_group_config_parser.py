from box import Box
from copy import deepcopy

from dae.configuration.config_parser_base import ConfigParserBase


class PeopleGroupConfigParser(ConfigParserBase):

    SECTION = 'peopleGroup'

    SPLIT_STR_LISTS = [
        'selectedPeopleGroupValues'
    ]

    FILTER_SELECTORS = {
        'peopleGroup': 'selectedPeopleGroupValues'
    }

    @staticmethod
    def _people_group_selectors_split_dict(dict_to_split):
        options = dict_to_split.split(':')
        return Box(
            {'id': options[0], 'name': options[1], 'color': options[2]},
            camel_killer_box=True, default_box=True, default_box_attr=None
        )

    @classmethod
    def _split_dict_lists(cls, dict_to_split):
        options = [cls._people_group_selectors_split_dict(el)
                   for el in cls._split_str_option_list(dict_to_split)]
        return options

    @staticmethod
    def _get_values(options):
        return {option['id']: option for option in options}

    @classmethod
    def _get_people_groups(cls, config):
        people_groups = {}

        for people_group_id, people_group in config.items():
            people_group['default'] = cls._people_group_selectors_split_dict(
                people_group['default'])
            people_group['domain'] = cls._split_dict_lists(
                people_group['domain'])
            people_group['values'] = cls._get_values(people_group['domain'])

            people_groups[people_group_id] = people_group

        return Box(
            people_groups, camel_killer_box=True, default_box=True,
            default_box_attr=None
        )

    @classmethod
    def get_config_description(cls, config):
        config = config.to_dict()

        result = {'peopleGroup': config.get('peopleGroup', {}).values()}

        return result

    @classmethod
    def parse(cls, config):
        config[cls.SECTION]['peopleGroup'] = deepcopy(config[cls.SECTION])
        config = super(PeopleGroupConfigParser, cls).parse(config)

        config[cls.SECTION]['peopleGroup'] = \
            cls._get_people_groups(config[cls.SECTION]['peopleGroup'])

        return config
