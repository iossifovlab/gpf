'''
Created on Nov 7, 2016

@author: lubo
'''
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()  # noqa

import os
from copy import deepcopy

from configurable_entities.configurable_entity_config import \
    ConfigurableEntityConfig


class EnrichmentConfig(ConfigurableEntityConfig):

    SPLIT_STR_LISTS = (
        'peopleGroups',
        'selectedBackgroundValues',
        'selectedCountingValues',
        'effect_types'
    )

    def __init__(self, config, *args, **kwargs):
        super(EnrichmentConfig, self).__init__(config, *args, **kwargs)

    def enrichment_cache_file(self, name=''):
        cache_file = os.path.join(
            os.path.split(self.config_file)[0],
            'enrichment-{}.pckl'.format(name)
        )

        return cache_file

    @staticmethod
    def _get_model(model_type, model_options, config):
        model = {}

        model['name'] = config.pop(model_type + '.name', None)
        model['id'] = model['name']
        model_file = config.pop(model_type + '.file', None)
        if model_file is None:
            model['filename'] = None
        else:
            model['filename'] = os.path.join(
                os.path.split(config['configFile'])[0],
                'enrichment/{}'.format(model_file)
            )
        model['desc'] = config.pop(model_type + '.desc', None)

        yield model

    @classmethod
    def _get_model_selectors(
            cls, enrichment_config, property_key, selected_property):
        print(enrichment_config)
        model_selector_elements = enrichment_config.get(
            selected_property, None)

        model_selector = cls._get_selectors(
            enrichment_config, property_key, cls._get_model,
            model_selector_elements
        )
        model_selector = {ms['id']: ms for ms in model_selector}

        return model_selector

    @classmethod
    def from_config(cls, config):
        if config is None:
            return
        study_config = config.study_config
        if study_config is None:
            return
        enrichment_config = \
            deepcopy(study_config.get('enrichment', None))
        if enrichment_config is None:
            return

        enrichment_config = cls.parse(enrichment_config)

        if enrichment_config.get('enabled', True) is False:
            return None

        enrichment_config['configFile'] = study_config.config_file

        enrichment_config['backgrounds'] = cls._get_model_selectors(
            enrichment_config, 'background', 'selectedBackgroundValues')
        enrichment_config['counting'] = cls._get_model_selectors(
            enrichment_config, 'counting', 'selectedCountingValues')

        return EnrichmentConfig(enrichment_config)
