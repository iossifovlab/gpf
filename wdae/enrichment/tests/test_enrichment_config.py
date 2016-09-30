'''
Created on Sep 29, 2016

@author: lubo
'''


import unittest

from enrichment.config import EnrichmentConfig


class EnrichmentConfigTest(unittest.TestCase):

    def test_effect_type_lgd(self):
        config = EnrichmentConfig('unaffected', 'LGDs')

        self.assertEquals('LGDs', config.effect_type)

    def test_bad_effect_type(self):
        with self.assertRaises(AssertionError):
            EnrichmentConfig('unaffected', 'ala bala')

    def test_missense_effect(self):
        config = EnrichmentConfig('unaffected', 'Missense')

        self.assertEquals('missense', config.effect_type)

    def test_synonymous_effect(self):
        config = EnrichmentConfig('unaffected', 'Synonymous')

        self.assertEquals('synonymous', config.effect_type)

#     def test_build_spec(self):
#         config = EnrichmentConfig('unaffected', 'LGDs')
#         spec = config.build_spec('M', rec=True)
#
#         self.assertIsNotNone(spec)
#         self.assertEquals("sib", spec['inchild'])
#         self.assertEquals('LGDs', spec['effect'])
#         self.assertEquals('rec', spec['type'])
#         self.assertEquals(
#             'sib|Rec LGDs|sib|male,female|Nonsense,Frame-shift,Splice-site',
#             spec['label'])
#
#         config = EnrichmentConfig('autism', 'LGDs')
#         spec = config.build_spec('M', rec=True)
#
#         self.assertIsNotNone(spec)
#         self.assertEquals("prb", spec['inchild'])
#         self.assertEquals('LGDs', spec['effect'])
#         self.assertEquals('rec', spec['type'])
#         self.assertEquals(
#             'prb|Rec LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',
#             spec['label'])
