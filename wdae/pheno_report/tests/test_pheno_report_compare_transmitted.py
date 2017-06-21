'''
Created on Apr 28, 2016

@author: lubo
'''
import unittest
from DAE import vDB
from transmitted.legacy_query import TransmissionLegacy
from transmitted.mysql_query import MysqlTransmittedQuery


class Test(unittest.TestCase):

    def test_experiment_with_mysql_families_with_variants(self):
        query = {
            'minParentsCalled': 0,
            'minAltFreqPrcnt': -1.0,
            'familyIds': None,
            'gender': None,
            'geneSyms': set(['POGZ']),
            'ultraRareOnly': False,
            'regionS': None,
            'effectTypes': ['missense'],
            'inChild': 'prb',
            'limit': None,
            'variantTypes': None,
            'presentInParent': ['father only'],
            'TMM_ALL': False,
            'presentInChild': None,
            'maxAltFreqPrcnt': 100.0}

        transmitted_study = vDB.get_study("w1202s766e611")
        impl = TransmissionLegacy(transmitted_study, "old")
        tfams = impl.get_families_with_transmitted_variants(**query)
        tfamilies = [f for f in tfams]
        self.assertEquals(42, len(tfamilies))

        try:
            m = MysqlTransmittedQuery(transmitted_study)

            tfams = m.get_families_with_transmitted_variants(**query)
            mfamilies = [f for f in tfams]
            self.assertEquals(42, len(mfamilies))

            self.assertEquals(set(tfamilies), set(mfamilies))
        except AssertionError:
            pass
