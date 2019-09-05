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

    @classmethod
    def _get_people_groups(cls, config, people_groups):
        people_groups_info = OrderedDict()
        for people_group_id, people_group in people_groups.items():
            if people_group_id not in config.peopleGroups:
                continue
            people_groups_info[people_group_id] = people_group

        return people_groups_info

    @staticmethod
    def _parse_data(config, cr_id):
        people_groups = config.get('peopleGroups', None)
        groups = config.get('groups', None)
        draw_all_families =\
            config.get('draw_all_families', False)
        count_of_families_for_show_id =\
            config.get('count_of_families_for_show_id', None)

        if people_groups is None or groups is None:
            return None
        if count_of_families_for_show_id is not None:
            count_of_families_for_show_id =\
                int(count_of_families_for_show_id)

        return OrderedDict([
            ('people_groups', people_groups),
            ('groups', OrderedDict([
                (group.split(':')[1].strip(),
                    group.split(':')[0].strip().split(','))
                for group in groups.split('|')])),
            ('draw_all_families', draw_all_families),
            ('families_count_show_id', count_of_families_for_show_id),
            ('id', cr_id),
        ])

    @classmethod
    def parse(cls, config):
        if config is None:
            return
        study_config = config.study_config
        config_section = deepcopy(study_config.get(cls.SECTION, None))
        config_section = \
            super(CommonReportsConfigParser, cls).parse_section(config_section)
        if not config_section:
            return None

        people_group = config.people_group_config.people_group

        people_groups_info = \
            cls._get_people_groups(config_section, people_group)
        filter_info = cls._parse_data(config_section, config.id)
        if filter_info is None:
            return None

        config_section.id = config.id

        config_section.effect_types = config_section.get('effect_types', [])
        config_section.effect_groups = config_section.get('effect_groups', [])

        config_file = study_config.get('config_file', '')
        assert os.path.exists(config_file)
        if config_section.get('file_path') is None:
            dirname = os.path.dirname(config_file)
            file_path = os.path.join(dirname, 'common_report.json')
            config_section.file_path = file_path

        config_section.people_groups_info = people_groups_info
        config_section.filter_info = filter_info

        return config_section
