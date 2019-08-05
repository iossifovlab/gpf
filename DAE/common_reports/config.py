import os

from box import Box
from collections import OrderedDict
from copy import deepcopy

from configuration.config_base import\
    ConfigurableEntityConfig


class CommonReportsConfig(object):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    def __init__(
            self, cr_id, config, people_groups_info, filter_info):
        self.config = config

        self.id = cr_id

        self.people_groups_info = people_groups_info
        self.filter_info = filter_info
        self.effect_groups = self.config.get('effect_groups', [])
        self.effect_types = self.config.get('effect_types', [])

        self.path = config.file


class CommonReportsParseConfig(ConfigurableEntityConfig):

    SPLIT_STR_LISTS = ('peopleGroups', 'effect_groups', 'effect_types')
    CAST_TO_BOOL = ('draw_all_families', 'enabled')

    @classmethod
    def _get_people_groups(cls, config, people_groups):
        people_groups_info = OrderedDict()
        for people_group in people_groups:
            if people_group['id'] not in config.peopleGroups:
                continue
            people_groups_info[people_group['id']] = people_group

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
    def from_config(cls, study_config):
        if not study_config:
            return None

        cr_id = study_config.id
        config = deepcopy(
            study_config.study_config.get('commonReport', None))
        config_file = study_config.study_config.get('config_file', '')

        if config is None:
            return None

        config = cls.parse(config)
        config = Box(config)

        if config.get('enabled', True) is False:
            return None

        people_group = study_config.people_group

        people_groups_info = \
            cls._get_people_groups(config, people_group)
        filter_info = cls._parse_data(config, cr_id)
        if filter_info is None:
            return None

        assert os.path.exists(config_file)

        if config.get('file') is None:
            dirname = os.path.dirname(config_file)
            filename = os.path.join(dirname, 'common_report.json')
            config.file = filename

        return CommonReportsConfig(
            cr_id, config, people_groups_info, filter_info)
