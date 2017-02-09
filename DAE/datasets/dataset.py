'''
Created on Feb 9, 2017

@author: lubo
'''


class Dataset(object):

    def __init__(self, dataset_descriptor):
        self.descriptor = dataset_descriptor

    def load(self):
        self.denovo_studies = self.query.get_denovo_studies(self.descriptor)
