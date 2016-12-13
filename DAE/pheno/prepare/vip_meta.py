'''
Created on Dec 13, 2016

@author: lubo
'''
from pheno.pheno_db import PhenoDB
from pheno.prepare.vip_families import VipLoader
from pheno.prepare.base_meta_variables import BaseMetaVariables


class VipMetaVariables(VipLoader, BaseMetaVariables):

    def __init__(self):
        super(VipMetaVariables, self).__init__()
        self.phdb = PhenoDB(self.pheno_db)
        self.phdb.load()
