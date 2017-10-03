'''
Created on Sep 18, 2017

@author: lubo
'''
import copy
from pheno.utils.configuration import PhenoConfig
from pheno.pheno_db import PhenoDB


class PhenoRegression(object):

    @staticmethod
    def build(dbname, config_filename=None):
        config = PhenoConfig.from_file(config_filename)
        pheno_db = PhenoDB(dbfile=config.get_dbfile(dbname))
        pheno_db.load()

        dbconfig = config.get_dbconfig(dbname)

        return PhenoRegression(dbconfig, pheno_db)

    def __init__(self, dbconfig, pheno_db):
        self.dbconfig = dbconfig
        self.pheno_db = pheno_db

        self.age = self._load_common_normalization_config(
            'age')
        self.nonverbal_iq = self._load_common_normalization_config(
            'nonverbal_iq')

    def _load_common_normalization_config(self, name):
        if name not in self.dbconfig:
            return None

        measure_id = self.dbconfig[name]
        parts = measure_id.split(':')
        if len(parts) == 1:
            instrument_name = None
            measure_name = parts[0]
        elif len(parts) == 2:
            instrument_name = parts[0]
            measure_name = parts[1]
        return {
            'name': name,
            'instrument_name': instrument_name,
            'measure_name': measure_name,
        }

    def _get_common_normalization_measure_id(
            self, base_measure_config, measure_id):
        if base_measure_config.get('instrument_name', None) is None:
            assert self.pheno_db.has_measure(measure_id)
            measure = self.pheno_db.get_measure(measure_id)
            base_measure_config['instrument_name'] = measure.instrument_name
        result_id = "{instrument_name}.{measure_name}".format(
            **base_measure_config)
        if self.pheno_db.has_measure(result_id):
            return result_id
        else:
            return None

    def get_age_measure_id(self, measure_id):
        age = copy.copy(self.age)
        return self._get_common_normalization_measure_id(
            age, measure_id)

    def get_nonverbal_iq_measure_id(self, measure_id):
        nonverbal_iq = copy.copy(self.nonverbal_iq)
        return self._get_common_normalization_measure_id(
            nonverbal_iq, measure_id)
