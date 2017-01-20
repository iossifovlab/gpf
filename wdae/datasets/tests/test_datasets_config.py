'''
Created on Jan 20, 2017

@author: lubo
'''

import unittest
from datasets.config import DatasetConfig


class DatasetsConfigTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(DatasetsConfigTest, cls).setUpClass()
        cls.dataset_config = DatasetConfig()

    def test_datasets_config_simple(self):
        datasets = self.dataset_config.get_datasets()

        self.assertIsNotNone(datasets)
        self.assertEquals(3, len(datasets))

    def test_phenotypes_simple(self):
        phenotypes = self.dataset_config.get_phenotypes()
        self.assertIsNotNone(phenotypes)
        self.assertEquals(11, len(phenotypes))

    def test_dataset_sd(self):
        ds = self.dataset_config.get_dataset('SD')
        self.assertIsNotNone(ds)

        self.assertIsNone(ds['phenoDB'])
        self.assertEquals(6, len(ds['phenotypes']))

    def test_dataset_ssc(self):
        ds = self.dataset_config.get_dataset('SSC')
        self.assertIsNotNone(ds)

        self.assertEquals('ssc', ds['phenoDB'])
        self.assertEquals(2, len(ds['phenotypes']))

    def test_dataset_not_found(self):
        ds = self.dataset_config.get_dataset('ala bala')
        self.assertIsNone(ds)
