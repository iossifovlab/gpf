'''
Created on Oct 23, 2015

@author: lubo
'''
from __future__ import absolute_import
from .variants_compare_base import VariantsCompareBase
from DAE import vDB
from transmitted.legacy_query import TransmissionLegacy
from transmitted.mysql_query import MysqlTransmittedQuery


def vs2l(vs):
    return [v for v in vs]


class Test(VariantsCompareBase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.transmitted_study = vDB.get_study("w1202s766e611")
        cls.legacy = TransmissionLegacy(cls.transmitted_study, "old")
        cls.mysql = MysqlTransmittedQuery(cls.transmitted_study)

    def test_compare_default_minus_one_single_gene(self):
        request = {
            "minParentsCalled": (-1),
            "maxAltFreqPrcnt": (-1),
            "minAltFreqPrcnt": (-1),
            "geneSyms": ['CHD8']
        }
        lvs = self.legacy.get_transmitted_variants(**request)
        mvs = self.mysql.get_transmitted_variants(**request)

        self.assertVariantsEquals(vs2l(lvs), vs2l(mvs),
                                  'default_minus_one_single_gene')

    def test_compare_minus_one_and_zero_single_gene(self):
        request = {
            "minParentsCalled": 0,
            "maxAltFreqPrcnt": (-1),
            "minAltFreqPrcnt": (-1),
            "geneSyms": ['CHD8']
        }
        lvs = self.legacy.get_transmitted_variants(**request)
        mvs = self.mysql.get_transmitted_variants(**request)

        self.assertVariantsEquals(vs2l(lvs), vs2l(mvs),
                                  'minus_one_and_zero_single_gene')

    def test_compare_zero_and_nozeros_single_gene(self):
        request = {
            "minParentsCalled": 0,
            "maxAltFreqPrcnt": 5,
            "minAltFreqPrcnt": 0,
            "geneSyms": ['CHD8']
        }
        lvs = self.legacy.get_transmitted_variants(**request)
        mvs = self.mysql.get_transmitted_variants(**request)

        self.assertVariantsEquals(vs2l(lvs), vs2l(mvs),
                                  'zero_and_nozeros_single_gene')

    def test_compare_zero_and_nozeros_again_single_gene(self):
        request = {
            "minParentsCalled": 0,
            "maxAltFreqPrcnt": 5,
            "minAltFreqPrcnt": 1,
            "geneSyms": ['CHD8']
        }
        lvs = self.legacy.get_transmitted_variants(**request)
        mvs = self.mysql.get_transmitted_variants(**request)

        self.assertVariantsEquals(vs2l(lvs), vs2l(mvs),
                                  'zero_and_nozeros_again_single_gene')

    def test_compare_intergenic_variants_in_single_family(self):
        request = {
            "minParentsCalled": 0,
            "maxAltFreqPrcnt": (-1),
            "minAltFreqPrcnt": (-1),
            "familyIds": ['11001'],
            "effectTypes": ['intergenic'],
        }
        lvs = self.legacy.get_transmitted_variants(**request)
        mvs = self.mysql.get_transmitted_variants(**request)

        self.assertVariantsEquals(
            vs2l(lvs), vs2l(mvs),
            'compare_intergenic_variants_in_single_family')
