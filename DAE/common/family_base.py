'''
Created on Mar 2, 2017

@author: lubo
'''


class FamilyQueryDelegate(object):

    def __init__(self, dataset):
        self.dataset = dataset
        assert self.dataset.pheno_db is not None
        assert self.dataset.families is not None
        assert self.dataset.persons is not None

        self.families = self.dataset.families
        self.persons = self.dataset.persons
        self.pheno_db = self.dataset.pheno_db
