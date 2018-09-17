'''
Created on Feb 27, 2017

@author: lubo
'''
from __future__ import unicode_literals
from datasets.dataset import Dataset


class SSCDataset(Dataset):

    def __init__(self, dataset_descriptor):
        super(SSCDataset, self).__init__(dataset_descriptor)
        assert self.name == 'SSC'
