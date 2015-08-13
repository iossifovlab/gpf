'''
Created on Aug 13, 2015

@author: lubo
'''
import unittest
from api.variants.hdf5_reindex import TransmissionQueryReindex


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.tquery = TransmissionQueryReindex('w1202s766e611')

    def setUp(self):
        pass

    def tearDown(self):
        pass

#     def test_check_all_family_variants(self):
#         tqr = self.tquery
#         frows = tqr.check_all_family_variants()
#         self.assertEquals(29375, len(frows))

    def test_build_index_for_family_variants(self):
        tqr = self.tquery
        tqr.build_index_for_family_variants()

#     def test_create_family_index(self):
#         tqr = self.tquery
#         tqr.create_family_index()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
