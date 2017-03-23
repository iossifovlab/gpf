'''
Created on Aug 23, 2016

@author: lubo
'''
import ConfigParser

from Config import Config
# import traceback


class PhenoConfig(object):

    def __init__(self, **kwargs):
        super(PhenoConfig, self).__init__()
        self.pheno_db = kwargs.get('pheno_db', 'ssc')
        config = kwargs.get('config', None)
        # print("PhenoConfig: config={}".format(config))
        # traceback.print_stack()

        if config:
            # print("using config argument...")
            assert isinstance(config, ConfigParser.SafeConfigParser)
            self.config = config
        else:
            dae_config = Config()
            wd = dae_config.daeDir
            self.config = ConfigParser.SafeConfigParser({'wd': wd})
            self.config.read(dae_config.phenoDBconfFile)

#         print("PhenoConfig: pheno_db={}; config={}".format(
#             self.pheno_db, self.config))
#     def __getitem__(self, args):
#         return self.config.get(*args)
