'''
Created on Jul 28, 2015

@author: lubo
'''
import unittest
from api.reports.variants import ReportBase


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_effect_types_base(self):
        et = ReportBase.effect_types()
        self.assertEqual(15, len(et),
                         "wrong number of effect types {}".format(len(et)))

    def test_effect_groups_base(self):
        eg = ReportBase.effect_groups()
        self.assertEqual(3, len(eg), "wrong number of effect groups")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
