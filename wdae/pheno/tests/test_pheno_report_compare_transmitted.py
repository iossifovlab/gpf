'''
Created on Apr 28, 2016

@author: lubo
'''
import unittest
from DAE import vDB
from transmitted.legacy_query import TransmissionLegacy


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
        fit = impl.get_families_with_transmitted_variants(**query)
        families = [f for f in fit]
        self.assertEquals(42, len(families))

if __name__ == "__main__":
    unittest.main()
