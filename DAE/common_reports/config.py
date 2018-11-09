from __future__ import unicode_literals
from builtins import object
from Config import Config
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
from box import Box

import common.config
from variants.attributes import Role


class CommonReportsConfig(object):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.dae_config = config

        wd = self.dae_config.daeDir
        data_dir = self.dae_config.data_dir

        config = ConfigParser({
            'wd': wd,
            'data': data_dir
        })
        config.read(self.dae_config.commonReportsConfFile)

        self.config = Box(common.config.to_dict(config), default_box=True,
                          default_box_attr=None)

    def _parse_data(self, data):
        parsed_data = {}
        for d in data.split(','):
            split_data = d.split(':')
            if len(split_data) == 1:
                split_data.append('phenotype')
            parsed_data[split_data[0]] = split_data[1]
        return parsed_data

    def _study_groups(self):
        return self._parse_data(self.config.CommonReports.study_groups)

    def _studies(self):
        return self._parse_data(self.config.CommonReports.studies)

    def _counters_roles(self):
        return [Role.from_name(role)
                for role in self.config.CommonReports.counters_role.split(',')]

    def _effect_groups(self):
        return self.config.CommonReports.effect_groups.split(',')

    def _effect_types(self):
        return self.config.CommonReports.effect_types.split(',')
