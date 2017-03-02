'''
Created on Feb 17, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from enrichment_api.views import EnrichmentModelsMixin


class Test(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.models = EnrichmentModelsMixin()

    def test_background_model_config_synonymous(self):
        query = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        background = self.models.get_background_model(query)
        self.assertIsNotNone(background)
        self.assertEquals('synonymousBackgroundModel', background.name)

    def test_background_model_config_coding_len(self):
        query = {
            'enrichmentBackgroundModel': 'codingLenBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        background = self.models.get_background_model(query)
        self.assertIsNotNone(background)
        self.assertEquals('codingLenBackgroundModel', background.name)

    def test_counting_model_config_gene(self):
        query = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        counting = self.models.get_counting_model(query)
        self.assertIsNotNone(counting)
        self.assertEquals('enrichmentGeneCounting', counting.name)

    def test_counting_model_config_events(self):
        query = {
            'enrichmentBackgroundModel': 'codingLenBackgroundModel',
            'enrichmentCountingModel': 'enrichmentEventsCounting',
        }
        counting = self.models.get_counting_model(query)
        self.assertIsNotNone(counting)
        self.assertEquals('enrichmentEventsCounting', counting.name)

    def test_enrichment_model_config(self):
        query = {
            'enrichmentBackgroundModel': 'samochaBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        model = self.models.get_enrichment_model(query)
        self.assertIsNotNone(model)
        self.assertIn('background', model)
        self.assertIn('counting', model)

        background = model.get('background')
        self.assertEquals('samochaBackgroundModel', background.name)
        counting = model.get('counting')
        self.assertEquals('enrichmentGeneCounting', counting.name)
