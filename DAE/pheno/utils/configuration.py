'''
Created on Aug 23, 2016

@author: lubo
'''
import os

from Config import Config
from DAE import vDB


class PhenoConfig(object):

    @staticmethod
    def get_all_ssc_studies():
        study_group = vDB.get_study_group('ALL SSC')
        denovo_studies = study_group.get_attr('studies')
        transmitted_studies = study_group.get_attr('transmittedStudies')
        studies = []
        studies.extend(vDB.get_studies(denovo_studies))
        studies.extend(vDB.get_studies(transmitted_studies))
        return studies

    def __init__(self):
        self.config = Config()
        self.v14 = self.config._daeConfig.get('sfariDB', 'v14')
        self.v15 = self.config._daeConfig.get('sfariDB', 'v15')
        self.cache_dir = self.config._daeConfig.get('sfariDB', 'cache')

        assert os.path.isdir(self.cache_dir)
        assert os.path.isdir(self.v14)
        assert os.path.isdir(self.v15)
