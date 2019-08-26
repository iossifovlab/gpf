'''
Created on Dec 8, 2016

@author: lubo
'''
import logging

from dae.configuration.configuration import DAEConfig
from dae.pheno.utils.configuration import PhenoConfig


LOGGER = logging.getLogger(__name__)


class PhenoFactory(object):

    def __init__(self, dae_config=None):
        super(PhenoFactory, self).__init__()
        if dae_config is None:
            dae_config = DAEConfig.read_and_parse_file_configuration()

        self.config = PhenoConfig.read_directory_configurations(
            dae_config.pheno_db.dir)

    def get_dbfile(self, dbname):
        return self.config[dbname].dbfile

    def get_dbconfig(self, dbname):
        return self.config[dbname]

    def has_pheno_db(self, dbname):
        return dbname in self.config

    def get_pheno_db_names(self):
        return list(self.config.keys())

    def get_pheno_db(self, dbname):
        if not self.has_pheno_db(dbname):
            raise ValueError("can't find pheno DB {}; available pheno DBs: {}"
                             .format(dbname, self.get_pheno_db_names()))
        from . import pheno_db
        LOGGER.info("loading pheno db <{}>".format(dbname))
        phdb = pheno_db.PhenoDB(dbfile=self.get_dbfile(dbname))
        phdb.load()
        return phdb
