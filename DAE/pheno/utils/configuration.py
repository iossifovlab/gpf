'''
Created on Aug 23, 2016

@author: lubo
'''
import os
from box import ConfigBox

from configuration.configuration import DAEConfig
from configuration.dae_config_parser import CaseSensitiveConfigParser, \
    DAEConfigParser

import common.config


def pheno_confbox(conf_path):
    config_parser = CaseSensitiveConfigParser(
        defaults={'wd': os.path.dirname(conf_path)})
    with open(conf_path, "r") as f:
        config_parser.read_file(f)
    return ConfigBox(common.config.to_dict(config_parser))


class PhenoConfig(object):

    @staticmethod
    def from_dae_config(dae_config):
        configs = [pheno_confbox(conf_path)
                   for conf_path in DAEConfigParser.
                   _collect_config_paths(dae_config.pheno_dir)]
        return PhenoConfig(configs)

    @staticmethod
    def from_file(filename=None):
        if filename is None:
            dae_config = DAEConfig.make_config()
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
            if 'phenoDB' in conf:
                name = conf['phenoDB'].name
                self.pheno_configs[name] = conf['phenoDB']
                if 'dbfile' in conf['phenoDB']:
                    assert os.path.isfile(self.get_dbfile(name)), \
                            self.get_dbfile(name)
                else:
                    conf['phenoDB'].dbfile = None
                if 'browser_dbfile' in conf['phenoDB']:
                    assert os.path.isfile(self.get_browser_dbfile(name)), \
                            self.get_browser_dbfile(name)
                else:
                    conf['phenoDB'].browser_dbfile = None
                if 'browser_images_dir' in conf['phenoDB']:
                    assert os.path.isdir(
                            self.get_browser_images_dir(name)), \
                                self.get_browser_images_dir(name)
                else:
                    conf['phenoDB'].browser_images_dir = None

    def __contains__(self, dbname):
        return dbname in self.pheno_configs

    @property
    def db_names(self):
        return list(self.pheno_configs.keys())

    def get_dbfile(self, dbname):
        if self.pheno_configs[dbname].dbfile is None:
            return None
        return os.path.join(self.pheno_configs[dbname].wd,
                            self.pheno_configs[dbname].dbfile)

    def get_dbconfig(self, dbname):
        return self.pheno_configs[dbname]

    def get_age(self, dbname):
        return self.pheno_configs[dbname].get('age', None)

    def get_nonverbal_iq(self, dbname):
        return self.pheno_configs[dbname].get('nonverbal_iq', None)

    def get_browser_dbfile(self, dbname):
        if self.pheno_configs[dbname].browser_dbfile is None:
            return None
        return os.path.join(self.pheno_configs[dbname].wd,
                            self.pheno_configs[dbname].browser_dbfile)

    def get_browser_images_dir(self, dbname):
        if self.pheno_configs[dbname].browser_images_dir is None:
            return None
        return os.path.join(self.pheno_configs[dbname].wd,
                            self.pheno_configs[dbname].browser_images_dir)

    def get_browser_images_url(self, dbname):
        return self.pheno_configs[dbname].get('browser_images_url', None)
