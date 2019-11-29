import logging

from dae.pheno.utils.config import PhenoConfigParser
from dae.pheno.pheno_db import PhenotypeDataStudy


LOGGER = logging.getLogger(__name__)


class PhenoDb(object):

    def __init__(self, dae_config):
        super(PhenoDb, self).__init__()
        assert dae_config

        self.config = PhenoConfigParser.read_directory_configurations(
            dae_config.pheno_db.dir)

    def get_dbfile(self, pheno_data_name):
        return self.config[pheno_data_name].dbfile

    def get_dbconfig(self, pheno_data_name):
        return self.config[pheno_data_name]

    def has_phenotype_data(self, pheno_data_name):
        return pheno_data_name in self.config

    def get_phenotype_data_names(self):
        return list(self.config.keys())

    def get_phenotype_data(self, pheno_data_name):
        if not self.has_phenotype_data(pheno_data_name):
            raise ValueError('cannot find phenotype data {};'
                             ' available phenotype data: {}'
                             .format(pheno_data_name,
                                     self.get_phenotype_data_names()))
        LOGGER.info('loading pheno db <{}>'.format(pheno_data_name))
        phenotype_data = PhenotypeDataStudy(
            dbfile=self.get_dbfile(pheno_data_name)
        )
        return phenotype_data
