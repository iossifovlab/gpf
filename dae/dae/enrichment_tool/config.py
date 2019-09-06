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

    FILTER_SELECTORS = {
        'background': 'selectedBackgroundValues',
        'counting': 'selectedCountingValues',
    }

    @staticmethod
    def enrichment_cache_file(config, name=''):
        cache_file = os.path.join(
            os.path.split(config.config_file)[0],
            'enrichment-{}.pckl'.format(name)
        )

        return cache_file

    @staticmethod
    def _get_model(model_config, config_file):
        for model_id in model_config.keys():
            model = model_config[model_id]

            model['id'] = model['name']

            model_file = model.get('file', None)
            if model_file is None:
                model['filename'] = None
            else:
                model['filename'] = os.path.join(
                    os.path.split(config_file)[0],
                    'enrichment/{}'.format(model_file)
                )

            model_config[model_id] = model

        return model_config

    @classmethod
    def parse(cls, config):
        if not config or not config.study_config or \
                not config.study_config.get(cls.SECTION, None):
            return None

        study_config = config.study_config
        config_section = deepcopy(study_config.get(cls.SECTION, None))
        config_section.config_file = study_config.config_file

        config_section = \
            super(EnrichmentConfigParser, cls).parse_section(config_section)
        if not config_section:
            return None

        config_section.backgrounds = cls._get_model(
            config_section.get('background', {}), config_section.config_file
        )
        config_section.counting = cls._get_model(
            config_section.get('counting', {}), config_section.config_file
        )

        return config_section
