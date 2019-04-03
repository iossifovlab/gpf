'''
Created on Aug 23, 2016

@author: lubo
'''
from __future__ import unicode_literals
import os

import reusables
from box import ConfigBox
# import traceback

from configurable_entities.configuration import DAEConfig


class PhenoConfig(ConfigBox):

    @staticmethod
    def from_dae_config(dae_config):
        filename = dae_config.pheno_conf
        conf = reusables.config_dict(
            filename,
            auto_find=False,
            verify=True,
            defaults={
                'wd': dae_config.dae_data_dir,
            })

        return PhenoConfig(conf)

    @staticmethod
    def from_file(filename=None):
        if filename is None:
            dae_config = DAEConfig()
            return PhenoConfig.from_dae_config(dae_config)

        wd = os.path.dirname(filename)
        conf = reusables.config_dict(
            filename,
            auto_find=False,
            verify=True,
            defaults={
                'wd': wd,
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

    def get_browser_dbfile(self, dbname):
        return self[dbname].browser_dbfile

    def get_browser_images_dir(self, dbname):
        return self[dbname].browser_images_dir

    def get_browser_images_url(self, dbname):
        return self[dbname].browser_images_url
