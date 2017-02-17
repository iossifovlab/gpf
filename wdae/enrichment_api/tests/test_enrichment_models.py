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

    def test_background_model_config(self):
        query = {
            'enrichmentModel': {
                'background': 'synonymousBackgroundModel',
                'counting': 'enrichmentEventsCounting'
            }
        }
        background = self.models.get_background_model(query)
        self.assertIsNotNone(background)

    def test_counting_model_config(self):
        query = {
            'enrichmentModel': {
                'background': 'synonymousBackgroundModel',
                'counting': 'enrichmentEventsCounting'
            }
        }
        counting = self.models.get_background_model(query)
        self.assertIsNotNone(counting)

    def test_enrichment_model_config(self):
        query = {
            'enrichmentModel': {
                'background': 'synonymousBackgroundModel',
                'counting': 'enrichmentEventsCounting'
            }
        }
        model = self.models.get_enrichment_model(query)
        self.assertIsNotNone(model)
        self.assertIn('background', model)
        self.assertIn('counting', model)
