'''
Created on Sep 18, 2017

@author: lubo
'''
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
