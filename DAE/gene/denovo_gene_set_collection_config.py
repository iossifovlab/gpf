import os
from copy import deepcopy

from configuration.config_base import ConfigBase
from variants.attributes import Sex


class DenovoGeneSetCollectionConfig(ConfigBase):
    SPLIT_STR_LISTS = (
        'peopleGroups',
        'standardCriterias',
        'standardCriteriasColumns',
        'recurrencyCriteria.segments',
        'geneSetsNames'
    )

    CAST_TO_BOOL = ('enabled')

    def __init__(self, config, *args, **kwargs):
        super(DenovoGeneSetCollectionConfig, self).__init__(
            config, *args, **kwargs)

    def denovo_gene_set_cache_file(self, people_group_id=''):
        cache_path = os.path.join(
            os.path.split(self.config_file)[0],
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
            from studies.helpers import expand_effect_types
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
            cls._standard_criterias_split_dict(
                standard_criteria_id, el.strip())
            for el in dict_to_split.split(',')
        ]
        return options

    @classmethod
    def _get_standard_criterias(
            cls, standard_criteria_type, standard_criteria_options,
            study_config):
        standard_criteria_id = standard_criteria_type.split('.')[-1]

        standard_criterias = cls._split_dict_lists(
            standard_criteria_id,
            study_config.pop(standard_criteria_type + '.segments')
        )

        yield standard_criterias

    @staticmethod
    def _get_recurrency_criterias(recurrency_criteria_segments):
        recurrency_criterias = {}
        for recurrency_criteria_str in recurrency_criteria_segments:
            name, from_count, to_count = \
                recurrency_criteria_str.strip().split(':')
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
            } for pg in people_group
            if pg.id in people_groups
        }

        return denovo_gene_sets

    @classmethod
    def from_config(cls, config):
        study_config = config.study_config
        config_section = deepcopy(study_config.get('denovoGeneSets', None))
        if config_section is None:
            return None

        config_section = cls.parse(config_section)

        if config.get('enabled', True) is False:
            return None

        config_section['id'] = config.id

        standard_criterias_elements = \
            config_section.get('standardCriteriasColumns', None)
        config_section['standardCriterias'] = cls._get_selectors(
            config_section, 'standardCriterias', cls._get_standard_criterias,
            standard_criterias_elements)

        config_section['recurrencyCriterias'] = cls._get_recurrency_criterias(
            config_section.get('recurrencyCriteria.segments', []))

        if 'peopleGroups' not in config_section or not \
                config_section['peopleGroups']:
            return None

        config_section['denovoGeneSets'] = cls._get_denovo_gene_sets(
            config.people_group, config_section['peopleGroups'])

        config_section['configFile'] = study_config.config_file

        return DenovoGeneSetCollectionConfig(config_section)
