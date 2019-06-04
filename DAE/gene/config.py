'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from future import standard_library
standard_library.install_aliases()  # noqa
import os
from copy import deepcopy

from configparser import ConfigParser
from GeneInfoDB import GeneInfoDB
from configurable_entities.configuration import DAEConfig

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class GeneInfoConfig(object):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    def __init__(self, config=None):
        if config is None:
            config = DAEConfig()
        self.dae_config = config

        wd = self.dae_config.dae_data_dir

        self.config = ConfigParser({
            'wd': wd,
        })
        with open(self.dae_config.gene_info_conf, "r") as infile:
            self.config.read_file(infile)

        self.gene_info = GeneInfoDB(
            self.dae_config.gene_info_conf,
            self.dae_config.dae_data_dir)


class DenovoGeneSetCollectionConfig(ConfigurableEntityConfig):
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
        value = options[1]
        if standard_criteria_id != 'sexes':
            value = value.split('.')

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

        return standard_criterias

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
