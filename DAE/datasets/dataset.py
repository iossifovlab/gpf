'''
Created on Feb 9, 2017

@author: lubo
'''
from DAE import pheno
from datasets.query import QueryDataset


class Dataset(object):

    def __init__(self, dataset_descriptor):
        self.descriptor = dataset_descriptor
        self.query = QueryDataset()
        self.denovo_studies = None
        self.transmitted_studies = None
        self.pheno_db = None
        self.families = None

    def load(self):
        self.denovo_studies = \
            self.query.get_denovo_studies(self.descriptor)
        self.transmitted_studies = \
            self.query.get_transmitted_studies(self.descriptor)
        self.pheno_db = self.load_pheno_db()

    def load_pheno_db(self):
        pheno_db = None
        if 'phenoDB' in self.descriptor:
            pheno_id = self.descriptor['phenoDB']
            if pheno.has_pheno_db(pheno_id):
                pheno_db = pheno.get_pheno_db(pheno_id)
        return pheno_db

    def load_families(self):
        families = {}
        for st in self.denovo_studies:
            families.update(st.families)
        for st in self.transmitted_studies:
            families.update(st.families)
        return families
