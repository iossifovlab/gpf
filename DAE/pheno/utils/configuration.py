'''
Created on Aug 23, 2016

@author: lubo
'''
from Config import Config
from DAE import vDB
import ConfigParser


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

    def __init__(self, config=None, *args, **kwargs):
        super(PhenoConfig, self).__init__(*args, **kwargs)

        if config is None:
            self.dae_config = Config()
        else:
            self.dae_config = config

        wd = self.dae_config.daeDir
        self.config = ConfigParser.SafeConfigParser({'wd': wd})
        self.config.read(self.dae_config.phenoDBconfFile)

    def __getitem__(self, args):
        return self.config.get(*args)
