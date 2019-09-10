from box import Box
from copy import deepcopy

from dae.configuration.config_parser_base import ConfigParserBase


class PeopleGroupConfigParser(ConfigParserBase):

    SECTION = 'peopleGroup'

    SPLIT_STR_LISTS = [
        'selectedPeopleGroupValues'
    ]

    FILTER_SELECTORS = {
        'peopleGroup': 'selectedPeopleGroupValues',
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
    def _parse_people_groups(cls, people_group_config):
        for people_group in people_group_config.values():
            people_group.default = cls._people_group_selectors_split_dict(
                people_group.default)
            people_group.domain = \
                cls._get_values(cls._split_dict_lists(people_group.domain))

        return people_group_config

    @classmethod
    def get_config_description(cls, config):
        config = config.to_dict()

        def domain_to_list(people_group):
            people_group['domain'] = list(people_group['domain'].values())
            return people_group

        people_groups = config.get(cls.SECTION, {}).values()
        people_groups = list(map(domain_to_list, people_groups))
        result = {cls.SECTION: people_groups}

        return result

    @classmethod
    def parse(cls, config):
        if not config or not config.get(cls.SECTION, None):
            return None

        config_section = deepcopy(config[cls.SECTION])
        config_section.peopleGroup = deepcopy(config_section)
        config_section = \
            super(PeopleGroupConfigParser, cls).parse_section(config_section)

        config_section.peopleGroup = \
            cls._parse_people_groups(config_section.people_group)

        return config_section
