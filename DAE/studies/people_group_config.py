from configurable_entities.configurable_entity_config import \
    ConfigurableEntityConfig


class PeopleGroupConfig(ConfigurableEntityConfig):

    SPLIT_STR_LISTS = [
        'columns'
    ]

    def __init__(self, config, *args, **kwargs):
        super(PeopleGroupConfig, self).__init__(config, *args, **kwargs)

    @property
    def people_group(self):
        if 'peopleGroup' in self:
            return self['peopleGroup']
        return []

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
    def _get_people_group(
            cls, people_group_type, people_group_options, study_config):
        people_group = {}

        people_group['name'] = \
            study_config.pop(people_group_type + '.name', None)
        people_group['source'] = \
            study_config.get(people_group_type + '.source', None)
        people_group['id'] = people_group_type
        people_group['default'] =\
            cls._people_group_selectors_split_dict(
                study_config.pop(people_group_type + '.default'))
        people_group['domain'] =\
            cls._split_dict_lists(
                study_config.pop(people_group_type + '.domain'))
        people_group['values'] =\
            cls._get_values(people_group['domain'])

        return people_group

    @classmethod
    def from_config(cls, config):
        config_section = config.get('peopleGroup', None)
        if config_section is None:
            return None

        config_section = cls.parse(config_section)

        people_group_elements = config_section.get('columns', None)
        people_group = cls._get_selectors(
            config_section, None, cls._get_people_group,
            people_group_elements
        )

        if people_group:
            config_section['peopleGroup'] = people_group

        return PeopleGroupConfig(config_section)

    @staticmethod
    def _get_description_keys():
        return [
            'peopleGroup'
        ]

    def get_config_description(self):
        keys = self._get_description_keys()
        config = self.to_dict()

        result = {key: config.get(key, None) for key in keys}

        return result
