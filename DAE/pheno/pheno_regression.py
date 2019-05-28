'''
Created on Sep 18, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
import copy
from pheno.utils.configuration import PhenoConfig
from pheno.pheno_db import PhenoDB
from configparser import ConfigParser
from os.path import isfile


class PhenoRegressions(dict):

    def __init__(self, confpath):
        conf_parser = ConfigParser()
        assert(isfile(confpath))
        conf_parser.read(confpath)

        for sec in conf_parser.sections():
            parts = sec.split('.')
            if parts[0] == 'regression':
                assert parts[1] not in self
                self[parts[1]] = dict(conf_parser[sec])

    def has_measure(self, measure_name, instrument_name):
        for _, reg in self.items():
            if measure_name == reg['measure_name']:
                if instrument_name and reg['instrument_name'] and \
                        instrument_name != reg['instrument_name']:
                    continue
                return True
        return False


class PhenoRegression(object):

    @staticmethod
    def build_from_config(dbname, config_filename=None):
        config = PhenoConfig.from_file(config_filename)
        pheno_db = PhenoDB(dbfile=config.get_dbfile(dbname))
        pheno_db.load()

        dbconfig = config.get_dbconfig(dbname)
        age = PhenoRegression._load_common_normalization_config(
            dbconfig, 'age')
        nonverbal_iq = PhenoRegression._load_common_normalization_config(
            dbconfig, 'nonverbal_iq')

        return PhenoRegression(pheno_db, age, nonverbal_iq)

    def __init__(self, pheno_db, age, nonverbal_iq):
        self.pheno_db = pheno_db
        self.age = age
        self.nonverbal_iq = nonverbal_iq

    @staticmethod
    def _load_common_normalization_config(dbconfig, name):
        if name not in dbconfig:
            return None

        measure_id = dbconfig[name]
        return PhenoRegression.build_common_normalization_config(
            name, measure_id)

    @staticmethod
    def build_common_normalization_config(name, measure_id):
        if measure_id is None:
            return None
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
        if self.age is None:
            return None
        age = copy.copy(self.age)
        return self._get_common_normalization_measure_id(
            age, measure_id)

    def get_nonverbal_iq_measure_id(self, measure_id):
        if self.nonverbal_iq is None:
            return None

        nonverbal_iq = copy.copy(self.nonverbal_iq)
        return self._get_common_normalization_measure_id(
            nonverbal_iq, measure_id)
