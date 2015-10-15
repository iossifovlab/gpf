'''
Created on Oct 15, 2015

@author: lubo
'''
import unittest
from mysql_transmitted_std_queries import dae_query_q101, mysql_query_q101
from mysql_transmitted_std_queries import dae_query_q201, mysql_query_q201
from mysql_transmitted_std_queries import dae_query_q301, mysql_query_q301
from mysql_transmitted_std_queries import dae_query_q401, mysql_query_q401
from mysql_transmitted_std_queries import dae_query_q501, mysql_query_q501
from mysql_transmitted_std_queries import dae_query_q601, mysql_query_q601


class Test(unittest.TestCase):

    def assertVariantStringAttribute(self, dv, mv, attr, msg):
        return self.assertEquals(
            dv.atts[attr], mv.atts[attr],
            "{}: {}: {}, {}".format(msg, attr,
                                    dv.atts[attr],
                                    mv.atts[attr]))

    def assertVariantIntAttribute(self, dv, mv, attr, msg):
        return self.assertEquals(
            int(dv.atts[attr]), mv.atts[attr],
            "{}: {}: {}, {}".format(msg, attr,
                                    dv.atts[attr],
                                    mv.atts[attr]))

    def assertVariantFloatAttribute(self, dv, mv, attr, msg):
        return self.assertEquals(
            float(dv.atts[attr]), mv.atts[attr],
            "{}: {}: {}, {}".format(msg, attr,
                                    dv.atts[attr],
                                    mv.atts[attr]))

    def assertVariantEquals(self, dv, mv, msg):
        self.assertVariantStringAttribute(dv, mv, "location", msg)
        self.assertVariantStringAttribute(dv, mv, "chr", msg)
        self.assertVariantIntAttribute(dv, mv, "position", msg)
        self.assertVariantStringAttribute(dv, mv, 'familyId', msg)
        self.assertVariantIntAttribute(dv, mv, "all.nParCalled", msg)
        self.assertVariantFloatAttribute(dv, mv, 'all.prcntParCalled', msg)
        self.assertVariantIntAttribute(dv, mv, "all.nAltAlls", msg)
        self.assertVariantFloatAttribute(dv, mv, 'all.altFreq', msg)
        self.assertVariantStringAttribute(dv, mv, 'variant', msg)
        self.assertVariantStringAttribute(dv, mv, 'bestState', msg)
        self.assertVariantStringAttribute(dv, mv, 'counts', msg)
        self.assertVariantStringAttribute(dv, mv, 'effectType', msg)
        # self.assertVariantStringAttribute(dv, mv, 'effectDetails', msg)

    def assertVariantsEquals(self, dvs, mvs, msg):
        self.assertEqual(len(dvs), len(mvs), "{}: len: {}, {}".
                         format(msg, len(dvs), len(mvs)))
        dvs.sort(key=lambda v: (v.location, v.familyId))
        mvs.sort(key=lambda v: (v.location, v.familyId))

        for i, dv in enumerate(dvs):
            mv = mvs[i]
            self.assertVariantEquals(dv, mv,
                                     "variant {} doesn't match".format(i))

    def test_compare_q101(self):
        dae_res = dae_query_q101()
        mysql_res = mysql_query_q101()

        self.assertVariantsEquals(dae_res, mysql_res, 'q101')

    def test_compare_q201(self):
        dae_res = dae_query_q201()
        mysql_res = mysql_query_q201()

        self.assertVariantsEquals(dae_res, mysql_res, 'q201')

    def test_compare_q301(self):
        dae_res = dae_query_q301()
        mysql_res = mysql_query_q301()

        self.assertVariantsEquals(dae_res, mysql_res, 'q301')

    def test_compare_q401(self):
        dae_res = dae_query_q401()
        mysql_res = mysql_query_q401()

        self.assertVariantsEquals(dae_res, mysql_res, 'q401')

    def test_compare_q501(self):
        dae_res = dae_query_q501()
        mysql_res = mysql_query_q501()

        self.assertVariantsEquals(dae_res, mysql_res, 'q501')

    def test_compare_q601(self):
        dae_res = dae_query_q601()
        mysql_res = mysql_query_q601()

        self.assertVariantsEquals(dae_res, mysql_res, 'q601')

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
