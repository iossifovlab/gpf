'''
Created on Nov 7, 2016

@author: lubo
'''
import os
from box import Box
from copy import deepcopy
from collections import OrderedDict

from configuration.dae_config_parser import DAEConfigParser


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class EnrichmentConfigParser(DAEConfigParser):

    SECTION = 'enrichment'

    SPLIT_STR_LISTS = (
        'peopleGroups',
        'selectedBackgroundValues',
        'selectedCountingValues',
        'effect_types'
    )

    @classproperty
    def PARSE_TO_DICT(cls):
        return {
            'backgrounds': {
                'group': 'background',
                'getter': cls._get_model,
                'selected': 'selectedBackgroundValues',
                'default': []
            }, 'counting': {
                'group': 'counting',
                'getter': cls._get_model,
                'selected': 'selectedCountingValues',
                'default': []
            }
        }

    @staticmethod
    def enrichment_cache_file(config, name=''):
        cache_file = os.path.join(
            os.path.split(config.config_file)[0],
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
                os.path.split(config.config_file)[0],
                'enrichment/{}'.format(model_file)
            )
        model['desc'] = config.pop(model_type + '.desc', None)

        yield model

    @staticmethod
    def _get_model_selectors(model_selector):
        return OrderedDict([(ms['id'], ms) for ms in model_selector])

    @classmethod
    def parse(cls, config):
        if config is None:
            return

        study_config = config.study_config
        if study_config is None:
            return

        enrichment_config = deepcopy(study_config.get(
            EnrichmentConfigParser.SECTION, None))
        if enrichment_config is None:
            return
        enrichment_config = Box(enrichment_config, camel_killer_box=True)

        enrichment_config['config_file'] = study_config.config_file

        enrichment_config = \
            super(EnrichmentConfigParser, cls).parse(enrichment_config)

        if enrichment_config.get('enabled', True) is False:
            return None

        enrichment_config['backgrounds'] = \
            cls._get_model_selectors(enrichment_config['backgrounds'])
        enrichment_config['counting'] = \
            cls._get_model_selectors(enrichment_config['counting'])
        enrichment_config['enrichment_cache_file'] = cls.enrichment_cache_file

        return enrichment_config
