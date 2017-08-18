'''
Created on Aug 23, 2016

@author: lubo
'''
import ConfigParser

from Config import Config
import os
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

    def get_dbfile(self, dbname=None):
        if dbname is None:
            dbfile = self.config.get(self.pheno_db, 'cache_file')
        else:
            dbfile = self.config.get(dbname, 'cache_file')

        if dbfile[0] != '/':
            dbfile = os.path.join(self.config.get('cache_dir', 'dir'), dbfile)
        return dbfile
