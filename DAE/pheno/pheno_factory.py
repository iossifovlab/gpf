'''
Created on Dec 8, 2016

@author: lubo
'''

from pheno.utils.configuration import PhenoConfig
import os


class PhenoFactory(PhenoConfig):

    def __init__(self):
        super(PhenoFactory, self).__init__()
        dbs = self.config.get('pheno', 'dbs')
        print("dbs: {}".format(dbs))
        available = [dbname.strip() for dbname in dbs.split(',')]
        print("available: {}".format(available))
        available = [dbname for dbname in available
                     if self._check_pheno_db(dbname)]
        self._available = set(available)

    def _check_pheno_db(self, dbname):
        assert self.config.has_section('cache_dir')
        assert self.config.has_option('cache_dir', 'dir')

        if not self.config.has_section(dbname):
            print("section: {} not found".format(dbname))
            return False
        if not self.config.has_option(dbname, 'cache_file'):
            print("section: {} option {} not found".format(
                dbname, 'cache_file'))
            return False
        dbfile = os.path.join(
            self.config.get('cache_dir', 'dir'),
            self.config.get(dbname, 'cache_file'))
        print("testing filename: {}".format(dbfile))
        if not os.path.isfile(dbfile):
            return False

        return True

    def has_pheno_db(self, dbname):
        return dbname in self._available

    def get_pheno_db_names(self):
        return [n for n in self._available]

    def get_pheno_db(self, dbname):
        if not self.has_pheno_db(dbname):
            raise ValueError("can't find pheno DB {}; available pheno DBs: {}"
                             .format(dbname, self._available))
        import pheno_db
        phdb = pheno_db.PhenoDB(pheno_db=dbname)
        phdb.load()
        return phdb
