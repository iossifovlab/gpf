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
            dae_config = DAEConfig.make_config()

        self.config = PhenoConfig.from_dae_config(dae_config)

    def get_dbfile(self, dbname):
        return self.config.get_dbfile(dbname)

    def get_dbconfig(self, dbname):
        return self.config.get_dbconfig(dbname)

    def has_pheno_db(self, dbname):
        return dbname in self.config

    def get_pheno_db_names(self):
        return self.config.db_names

    def get_pheno_db(self, dbname):
        if not self.has_pheno_db(dbname):
            raise ValueError("can't find pheno DB {}; available pheno DBs: {}"
                             .format(dbname, self.get_pheno_db_names()))
        from . import pheno_db
        LOGGER.info("loading pheno db <{}>".format(dbname))
        phdb = pheno_db.PhenoDB(dbfile=self.get_dbfile(dbname))
        phdb.load()
        return phdb
