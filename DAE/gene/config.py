'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from Config import Config
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
from GeneInfoDB import GeneInfoDB


class GeneInfoConfig(object):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.dae_config = config

        wd = self.dae_config.daeDir
        data_dir = self.dae_config.data_dir

        self.config = ConfigParser({
            'wd': wd,
            'data': data_dir
        })
        self.config.read(self.dae_config.geneInfoDBconfFile)
        self.gene_info = GeneInfoDB(
            self.dae_config.geneInfoDBconfFile,
            self.dae_config.daeDir,
            self.dae_config.data_dir)
