'''
Created on Sep 29, 2016

@author: lubo
'''


import unittest

from enrichment.config import EnrichmentConfig


class EnrichmentConfigTest(unittest.TestCase):

    def test_effect_type_lgd(self):
        config = EnrichmentConfig('unaffected', 'LGDs')

        assert ['LGDs'] == config.effect_types

    def test_bad_effect_type(self):
        with self.assertRaises(AssertionError):
            EnrichmentConfig('unaffected', 'ala bala')

    def test_missense_effect(self):
        config = EnrichmentConfig('unaffected', 'Missense')

        assert ['missense'] == config.effect_types

    def test_synonimous_effect(self):
        config = EnrichmentConfig('unaffected', 'Synonymous')

        assert ['synonymous'] == config.effect_types
