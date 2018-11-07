from __future__ import unicode_literals
from builtins import object
from Config import Config
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
from box import Box

import common.config


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

    def _datasets(self):
        return self.config.CommonReports.datasets.split(',')

    def _study_groups(self):
        return self.config.CommonReports.study_groups.split(',')

    def _studies(self):
        return self.config.CommonReports.studies.split(',')
