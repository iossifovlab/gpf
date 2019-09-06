import os

from collections import OrderedDict
from copy import deepcopy

from dae.configuration.config_parser_base import ConfigParserBase


class CommonReportsConfigParser(ConfigParserBase):

    SECTION = 'commonReport'

    SPLIT_STR_LISTS = (
        'peopleGroups',
        'effect_groups',
        'effect_types',
    )

    CAST_TO_BOOL = (
        'draw_all_families',
    )

    CAST_TO_INT = (
        'families_count_show_id',
    )

    FILTER_SELECTORS = {
        'people_groups_info': 'peopleGroups'
    }

    @classmethod
    def parse(cls, config):
        if config is None or cls.SECTION not in config.study_config:
            return None

        study_config = config.study_config
        config_section = deepcopy(study_config.get(cls.SECTION, None))
        config_section.people_groups_info = \
            config.people_group_config.people_group

        config_section = \
            super(CommonReportsConfigParser, cls).parse_section(config_section)
        if config_section is None or config_section.people_groups is None or \
                config_section.groups is None:
            return None

        config_section.id = config.id

        config_section.draw_all_families = \
            config_section.get('draw_all_families', False)

        config_section.groups = OrderedDict([
            (group.split(':')[1].strip(),
             group.split(':')[0].strip().split(','))
            for group in config_section.groups.split('|')
        ])

        config_section.effect_types = config_section.get('effect_types', [])
        config_section.effect_groups = config_section.get('effect_groups', [])

        config_file = study_config.get('config_file', '')
        assert os.path.exists(config_file)
        if config_section.get('file_path') is None:
            dirname = os.path.dirname(config_file)
            file_path = os.path.join(dirname, 'common_report.json')
            config_section.file_path = file_path

        return config_section
