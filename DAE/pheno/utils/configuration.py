'''
Created on Aug 23, 2016

@author: lubo
'''
import ConfigParser

from Config import Config


class PhenoConfig(object):

    def __init__(self, **kwargs):
        super(PhenoConfig, self).__init__()
        self.pheno_db = kwargs.get('pheno_db', 'ssc')
        config = kwargs.get('config', None)

        if config:
            assert isinstance(config, ConfigParser.SafeConfigParser)
            self.config = config
        else:
            dae_config = Config()
            wd = dae_config.daeDir
            self.config = ConfigParser.SafeConfigParser({'wd': wd})
            self.config.read(dae_config.phenoDBconfFile)

#     def __getitem__(self, args):
#         return self.config.get(*args)
