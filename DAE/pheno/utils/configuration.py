'''
Created on Aug 23, 2016

@author: lubo
'''
import os

from Config import Config


class PhenoConfig(object):

    def __init__(self):
        self.config = Config()
        self.v14 = self.config._daeConfig.get('sfariDB', 'v14')
        self.v15 = self.config._daeConfig.get('sfariDB', 'v15')
        self.cache_dir = self.config._daeConfig.get('sfariDB', 'cache')

        assert os.path.isdir(self.cache_dir)
        assert os.path.isdir(self.v14)
        assert os.path.isdir(self.v15)
