'''
Created on Jul 4, 2013

@author: leotta
'''
from __future__ import unicode_literals, print_function, absolute_import
from future import standard_library
standard_library.install_aliases()  # noqa

import os
from builtins import object
from configparser import ConfigParser


class Config(object):

    def __init__(self):
        self._dae_data_dir = os.environ.get('DAE_DATA_DIR', None)
        self._daeDir = os.environ['DAE_DB_DIR']

        self._daeConfig = ConfigParser({
            'wd': self._daeDir,
            'data': self._dae_data_dir
        })
        self._daeConfig.optionxform = lambda x: x
        self._daeConfig.read(
            os.path.join(self._daeDir, "DAE.conf"),
            encoding="ascii"
        )

        # self._phenoDBFile = self._daeConfig.get('phenoDB', 'file')

        self._phenoDBconfFile = self._daeConfig.get('phenoDB', 'confFile')
        self._phenoDBdir = self._daeConfig.get('phenoDB', 'dir')

        # self._sfariDBdir = self._daeConfig.get('sfariDB', 'dir')

        self._geneInfoDBdir = self._daeConfig.get('geneInfoDB', 'dir')
        self._geneInfoDBconfFile = self._daeConfig.get(
            'geneInfoDB', 'confFile')
        self._genomicScoresDBdir = self._daeConfig.get(
            'genomicScoresDB', 'dir')
        self._genomicScoresDBconfFile = self._daeConfig.get(
            'genomicScoresDB', 'confFile')
        self._variantsDBdir = self._daeConfig.get('variantsDB', 'dir')
        self._variantsDBconfFile = self._daeConfig.get(
            'variantsDB', 'confFile')
        self._genomesDBconfFile = self._daeConfig.get('genomesDB', 'confFile')

        self._enrichmentConfFile = self._daeConfig.get(
            'enrichment', 'confFile')

        self._commonReportsConfFile = self._daeConfig.get(
            'commonReports', 'confFile')

    @property
    def daeDir(self):
        return self._daeDir

    @property
    def data_dir(self):
        return self._dae_data_dir

#     @property
#     def phenoDBFile(self):
#         return self._phenoDBFile

    @property
    def phenoDBdir(self):
        return self._phenoDBdir

    @property
    def phenoDBconfFile(self):
        return self._phenoDBconfFile

    @property
    def sfariDBdir(self):
        return self._sfariDBdir

    @property
    def geneInfoDBdir(self):
        return self._geneInfoDBdir

    @property
    def geneInfoDBconfFile(self):
        return self._geneInfoDBconfFile

    @property
    def genomicScoresDBdir(self):
        return self._genomicScoresDBdir

    @property
    def genomicScoresDBconfFile(self):
        return self._genomicScoresDBconfFile

    @property
    def variantsDBdir(self):
        return self._variantsDBdir

    @property
    def variantsDBconfFile(self):
        return self._variantsDBconfFile

    @property
    def genomesDBconfFile(self):
        return self._genomesDBconfFile

    @property
    def enrichmentConfFile(self):
        return self._enrichmentConfFile

    @property
    def commonReportsConfFile(self):
        return self._commonReportsConfFile
