'''
Created on Dec 8, 2016

@author: lubo
'''

from pheno.utils.configuration import PhenoConfig


class PhenoFactory(object):

    def __init__(self, config_filename=None):
        super(PhenoFactory, self).__init__()
        self.config = PhenoConfig.from_file(config_filename)

    def get_dbfile(self, dbname):
        return self.config.get_dbfile(dbname)

    def get_dbconfig(self, dbname):
        return self.config.get_dbconfig(dbname)

    def has_pheno_db(self, dbname):
        return dbname in self.config.pheno.list("dbs")

    def get_pheno_db_names(self):
        return self.config.pheno.list("dbs")[:]

    def get_pheno_db(self, dbname):
        if not self.has_pheno_db(dbname):
            raise ValueError("can't find pheno DB {}; available pheno DBs: {}"
                             .format(dbname, self.get_pheno_db_names()))
        import pheno_db
        phdb = pheno_db.PhenoDB(dbfile=self.get_dbfile(dbname))
        phdb.load()
        return phdb
