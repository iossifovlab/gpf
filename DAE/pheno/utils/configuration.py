'''
Created on Aug 23, 2016

@author: lubo
'''

from Config import Config
import reusables
from box import ConfigBox
# import traceback


class PhenoConfig(ConfigBox):

    @staticmethod
    def from_file(filename=None):
        if filename is None:
            dae_config = Config()
            wd = dae_config.daeDir
            data_dir = dae_config.data_dir
            filename = dae_config.phenoDBconfFile
        if not isinstance(filename, str):
            filename = str(filename)

        conf = reusables.config_dict(
            filename,
            auto_find=False,
            verify=True,
            defaults={
                'wd': wd,
                'data': data_dir,
            })

        return PhenoConfig(conf)

    @staticmethod
    def from_dict(data):
        return PhenoConfig(data)

    def __init__(self, data, **kwargs):
        super(PhenoConfig, self).__init__(data, **kwargs)

    def get_dbfile(self, dbname):
        assert dbname in self.pheno.list("dbs")

        dbfile = self[dbname].dbfile
        return dbfile

    def get_dbconfig(self, dbname):
        assert dbname in self.pheno.list("dbs")
        return self[dbname]

    def get_age(self, dbname):
        return self[dbname].age

    def get_nonverbal_iq(self, dbname):
        return self[dbname].nonverbal_iq
