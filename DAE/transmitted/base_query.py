'''
Created on Oct 23, 2015

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from future import standard_library
standard_library.install_aliases()  # noqa

from configparser import NoOptionError


class TransmissionConfig(object):

    def __init__(self, study, call_set=None):
        assert study.has_transmitted

        self.study = study
        self._call_set = call_set

        self._config = self.study.vdb._config
        self._config_section = self.study._configSection

    def _get_config_path(self, name):
        if self._call_set == 'default' or self._call_set is None:
            path = ['transmittedVariants', name]
        else:
            path = ['transmittedVariants', self._call_set, name]
        return '.'.join(path)

    def _get_params(self, name):
        path = self._get_config_path(name)
        try:
            result = self._config.get(self._config_section, path)
        except NoOptionError:
            result = None
        return result
