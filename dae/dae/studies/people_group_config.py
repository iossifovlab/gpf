from dae.configuration.dae_config_parser import DAEConfigParser


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class PeopleGroupConfig(DAEConfigParser):

    SECTION = 'peopleGroup'

    SPLIT_STR_LISTS = [
        'selectedPeopleGroupValues'
    ]

    @classproperty
    def PARSE_TO_DICT(cls):
        return {
            'peopleGroup': {
                'group': None,
                'getter': cls._get_people_group,
                'selected': 'selectedPeopleGroupValues',
                'default': []
            }
        }

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

        people_group['id'] = people_group_type
        people_group['name'] = \
            study_config.pop(people_group_type + '.name', None)
        people_group['source'] = \
            study_config.get(people_group_type + '.source', None)
        people_group['default'] = cls._people_group_selectors_split_dict(
                study_config.pop(people_group_type + '.default'))
        people_group['domain'] = cls._split_dict_lists(
            study_config.pop(people_group_type + '.domain'))
        people_group['values'] = cls._get_values(people_group['domain'])

        yield people_group

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
