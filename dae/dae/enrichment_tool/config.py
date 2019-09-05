'''
Created on Nov 7, 2016

@author: lubo
'''
import os
from copy import deepcopy

from dae.configuration.config_parser_base import ConfigParserBase


class EnrichmentConfigParser(ConfigParserBase):

    SECTION = 'enrichment'

    SPLIT_STR_LISTS = (
        'peopleGroups',
        'selectedBackgroundValues',
        'selectedCountingValues',
        'effect_types'
    )

    @staticmethod
    def enrichment_cache_file(config, name=''):
        cache_file = os.path.join(
            os.path.split(config.config_file)[0],
            'enrichment-{}.pckl'.format(name)
        )

        return cache_file

    @staticmethod
    def _get_model(config, group, selected):
        selected_elements = config.get(selected, None)
        models = {}

        for model_id in config.get(group, {}).keys():
            if selected_elements and model_id not in selected_elements:
                continue

            model = config[group][model_id]
            if not isinstance(model, dict):
                continue

            model['id'] = model['name']

            model_file = model.get('file', None)
            if model_file is None:
                model['filename'] = None
            else:
                model['filename'] = os.path.join(
                    os.path.split(config.config_file)[0],
                    'enrichment/{}'.format(model_file)
                )

            models[model_id] = model

        return models

    @classmethod
    def parse(cls, config):
        if config is None:
            return

        study_config = config.study_config
        if study_config is None:
            return

        enrichment_config = deepcopy(study_config.get(cls.SECTION, None))
        if enrichment_config is None:
            return
        enrichment_config['config_file'] = study_config.config_file

        enrichment_config = \
            super(EnrichmentConfigParser, cls).parse_section(enrichment_config)
        if not enrichment_config:
            return None

        enrichment_config['backgrounds'] = cls._get_model(
            enrichment_config, 'background', 'selectedBackgroundValues')
        enrichment_config['counting'] = cls._get_model(
            enrichment_config, 'counting', 'selectedCountingValues')

        return enrichment_config
