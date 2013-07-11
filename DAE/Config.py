'''
Created on Jul 4, 2013

@author: leotta
'''
import os
import ConfigParser

# adds exceptions for error handling 
class Config:

    def __init__(self):
        
        self._daeDir = os.environ['DAE_DB_DIR']
        
        self._daeConfig = ConfigParser.SafeConfigParser({'wd':self._daeDir})
        self._daeConfig.optionxform = lambda x: x
        self._daeConfig.read(os.path.join(self._daeDir,"DAE.conf"))

        self._phenoDBFile = self._daeConfig.get('phenoDB', 'file')
        self._sfariDBdir= self._daeConfig.get('sfariDB', 'dir')
        self._geneInfoDBdir = self._daeConfig.get('geneInfoDB', 'dir')
        self._geneInfoDBconfFile = self._daeConfig.get('geneInfoDB', 'confFile')
        self._variantsDBdir = self._daeConfig.get('variantsDB', 'dir')
        self._variantsDBconfFile = self._daeConfig.get('variantsDB', 'confFile')

    @property
    def daeDir(self):
        return self._daeDir

    @property
    def phenoDBFile(self):
        return self._phenoDBFile
        
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
    def variantsDBdir(self):
        return self._variantsDBdir
        
    @property
    def variantsDBconfFile(self):
        return self._variantsDBconfFile

