'''
Created on Aug 23, 2016

@author: lubo
'''
from Config import Config
import DAE
import ConfigParser


class PhenoConfig(object):

    @staticmethod
    def get_all_ssc_studies():
        study_group = DAE.vDB.get_study_group('ALL SSC')
        denovo_studies = study_group.get_attr('studies')
        transmitted_studies = study_group.get_attr('transmittedStudies')
        studies = []
        studies.extend(DAE.vDB.get_studies(denovo_studies))
        studies.extend(DAE.vDB.get_studies(transmitted_studies))
        return studies

    def __init__(self, dae_config=None, config=None, *args, **kwargs):
        super(PhenoConfig, self).__init__(*args, **kwargs)
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
