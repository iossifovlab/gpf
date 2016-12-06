'''
Created on Aug 23, 2016

@author: lubo
'''
from Config import Config
import ConfigParser


class PhenoConfig(object):

    def __init__(self, **kwargs):
        super(PhenoConfig, self).__init__()
        self.pheno_db = kwargs.get('pheno_db', 'ssc_v15')
        dae_config = kwargs.get('dae_config', None)
        config = kwargs.get('config', None)

        if dae_config is None:
            self.dae_config = Config()
        else:
            self.dae_config = dae_config

        if config:
            assert isinstance(config, ConfigParser.SafeConfigParser)
            self.config = config
        else:
            wd = self.dae_config.daeDir
            self.config = ConfigParser.SafeConfigParser({'wd': wd})
            self.config.read(self.dae_config.phenoDBconfFile)

    def __getitem__(self, args):
        return self.config.get(*args)
