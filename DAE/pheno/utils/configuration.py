'''
Created on Aug 23, 2016

@author: lubo
'''
from __future__ import unicode_literals

import os
import reusables
from box import ConfigBox

from configurable_entities.configuration import DAEConfig
from configurable_entities.configurable_entity_definition import \
        ConfigurableEntityDefinition


def pheno_confbox(conf_path):
    return ConfigBox(reusables.config_dict(conf_path,
                     auto_find=False, verify=True,
                     defaults={'wd': os.path.dirname(conf_path)}))


class PhenoConfig(object):

    @staticmethod
    def from_dae_config(dae_config):
        configs = [pheno_confbox(conf_path)
                   for conf_path in ConfigurableEntityDefinition.
                   _collect_config_paths(dae_config.pheno_dir)]
        return PhenoConfig(configs)

    @staticmethod
    def from_file(filename=None):
        if filename is None:
            dae_config = DAEConfig()
            return PhenoConfig.from_dae_config(dae_config)
        return PhenoConfig([pheno_confbox(filename)])

    def __init__(self, configs):
        class PhenoConfDict(dict):
            """
                Custom dict that additionally prints the
                dict's keys when a key lookup fails.
            """
            def __missing__(self, key):
                raise KeyError(key, self.keys())

        self.pheno_configs = PhenoConfDict()
        for conf in configs:
            self.pheno_configs[conf['general'].name] = conf['general']

    def __contains__(self, dbname):
        return dbname in self.pheno_configs

    @property
    def db_names(self):
        return list(self.pheno_configs.keys())

    def get_dbfile(self, dbname):
        return os.path.join(self.pheno_configs[dbname].wd,
                            self.pheno_configs[dbname].dbfile)

    def get_dbconfig(self, dbname):
        return self.pheno_configs[dbname]

    def get_age(self, dbname):
        return self.pheno_configs[dbname].age

    def get_nonverbal_iq(self, dbname):
        return self.pheno_configs[dbname].nonverbal_iq

    def get_browser_dbfile(self, dbname):
        return os.path.join(self.pheno_configs[dbname].wd,
                            self.pheno_configs[dbname].browser_dbfile)

    def get_browser_images_dir(self, dbname):
        return os.path.join(self.pheno_configs[dbname].wd,
                            self.pheno_configs[dbname].browser_images_dir)

    def get_browser_images_url(self, dbname):
        return self.pheno_configs[dbname].browser_images_url
