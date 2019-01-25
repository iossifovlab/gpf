'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from future import standard_library
standard_library.install_aliases()  # noqa

from configparser import ConfigParser
from GeneInfoDB import GeneInfoDB
from configurable_entities.configuration import DAEConfig


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
