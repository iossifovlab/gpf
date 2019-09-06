import os
from copy import deepcopy

from dae.configuration.config_parser_base import ConfigParserBase
from dae.variants.attributes import Sex


class DenovoGeneSetConfigParser(ConfigParserBase):

    SECTION = 'denovoGeneSets'

    SPLIT_STR_LISTS = (
        'peopleGroups',
        'selectedStandardCriteriasValues',
        'geneSetsNames'
    )

    FILTER_SELECTORS = {
        'standardCriterias': 'selectedStandardCriteriasValues'
    }

    @staticmethod
    def denovo_gene_set_cache_file(config, people_group_id=''):
        cache_path = os.path.join(
            os.path.split(config.config_file)[0],
            'denovo-cache-' + people_group_id + '.json'
        )

        return cache_path

    @staticmethod
    def _standard_criterias_split_dict(standard_criteria_id, dict_to_split):
        options = dict_to_split.split(':')
        value = options[1].split('.')

        # TODO: Remove this when study.query_variants can support non
        # expand_effect_types as LGDs
        if standard_criteria_id == 'effect_types':
            from dae.studies.helpers import expand_effect_types
            value = expand_effect_types(value)
        elif standard_criteria_id == 'sexes':
            value = [Sex.from_name(v) for v in value]

        return {
            'property': standard_criteria_id,
            'name': options[0],
            'value': value
        }

    @classmethod
    def _split_dict_lists(cls, standard_criteria_id, dict_to_split):
        options = [
            cls._standard_criterias_split_dict(standard_criteria_id, el)
            for el in cls._split_str_option_list(dict_to_split)
        ]
        return options

    @classmethod
    def _get_standard_criterias(cls, config):
        result = []

        standard_criterias = config.get('standardCriterias', {})

        for sc_id, sc in standard_criterias.items():
            standard_criteria = \
                cls._split_dict_lists(sc_id, sc.pop('segments'))

            result.append(standard_criteria)

        config['standardCriterias'] = result

        return config

    @classmethod
    def _get_recurrency_criterias(cls, recurrency_criteria_segments):
        recurrency_criterias = {}
        for recurrency_criteria_str in \
                cls._split_str_option_list(recurrency_criteria_segments):
            name, from_count, to_count = recurrency_criteria_str.split(':')
            recurrency_criterias[name] = {
                'from': int(from_count),
                'to': int(to_count)
            }

        return recurrency_criterias

    @staticmethod
    def _get_denovo_gene_sets(people_group, people_groups):
        if len(people_group) == 0:
            return None

        if not people_groups or (people_groups and len(people_groups) == 0):
            return None

        denovo_gene_sets = {
            pg.id: {
                'name': pg.name,
                'source': pg.source
            } for pg in people_group.values()
            if pg.id in people_groups
        }

        return denovo_gene_sets

    @classmethod
    def parse(cls, config):
        if config is None:
            return None

        study_config = config.study_config
        if study_config is None:
            return None

        config_section = deepcopy(study_config.get(cls.SECTION, None))
        config_section = super(DenovoGeneSetConfigParser, cls). \
            parse_section(config_section)
        if config_section is None:
            return None

        config_section['id'] = config.id

        config_section = cls._get_standard_criterias(config_section)

        config_section['recurrencyCriterias'] = cls._get_recurrency_criterias(
            config_section.get('recurrencyCriteria', {}).get('segments', []))

        if 'peopleGroups' not in config_section or not \
                config_section['peopleGroups']:
            return None

        config_section['denovoGeneSets'] = cls._get_denovo_gene_sets(
            config.people_group_config.people_group,
            config_section['peopleGroups']
        )

        config_section['configFile'] = study_config.config_file

        return config_section
