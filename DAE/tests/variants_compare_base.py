'''
Created on Oct 23, 2015

@author: lubo
'''
import unittest


class VariantsCompareBase(unittest.TestCase):

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
        self.assertVariantStringAttribute(dv, mv, 'effectDetails', msg)

    def assertVariantsEquals(self, dvs, mvs, msg):
        self.assertEqual(len(dvs), len(mvs), "{}: len: {}, {}".
                         format(msg, len(dvs), len(mvs)))
        dvs.sort(key=lambda v: (v.location, v.familyId))
        mvs.sort(key=lambda v: (v.location, v.familyId))

        for i, dv in enumerate(dvs):
            mv = mvs[i]
            self.assertVariantEquals(dv, mv,
                                     "variant {} doesn't match".format(i))
