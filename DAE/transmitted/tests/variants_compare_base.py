'''
Created on Oct 23, 2015

@author: lubo
'''
from __future__ import unicode_literals
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
            int(dv.atts[attr]), int(mv.atts[attr]),
            "{}: {}: {}, {}".format(msg, attr,
                                    dv.atts[attr],
                                    mv.atts[attr]))

    def assertVariantFloatAttribute(self, dv, mv, attr, msg):
        return self.assertEquals(
            float(dv.atts[attr]), float(mv.atts[attr]),
            "{}: {}: {}, {}".format(msg, attr,
                                    dv.atts[attr],
                                    mv.atts[attr]))

    def assertVariantProperty(self, dv, mv, prop, msg):
        dval = getattr(dv, prop)
        mval = getattr(mv, prop)
        self.assertEqual(
            dval,
            mval,
            "{}: {}: {}, {}".format(msg, prop,
                                    dval,
                                    mval))

    def assertSummaryVariantEquals(self, dv, mv, msg):
        self.assertVariantStringAttribute(dv, mv, "location", msg)
        self.assertVariantStringAttribute(dv, mv, "chr", msg)
        self.assertVariantIntAttribute(dv, mv, "position", msg)
        self.assertVariantIntAttribute(dv, mv, "all.nParCalled", msg)
        self.assertVariantFloatAttribute(dv, mv, 'all.prcntParCalled', msg)
        self.assertVariantIntAttribute(dv, mv, "all.nAltAlls", msg)
        self.assertVariantFloatAttribute(dv, mv, 'all.altFreq', msg)
        self.assertVariantStringAttribute(dv, mv, 'variant', msg)
        self.assertVariantStringAttribute(dv, mv, 'effectType', msg)
        self.assertVariantStringAttribute(dv, mv, 'effectDetails', msg)
        self.assertVariantProperty(dv, mv, 'requestedGeneEffects', msg)

    def assertVariantEquals(self, dv, mv, msg):
        self.assertSummaryVariantEquals(dv, mv, msg)
        self.assertVariantStringAttribute(dv, mv, 'familyId', msg)
        self.assertVariantStringAttribute(dv, mv, 'bestState', msg)
        self.assertVariantStringAttribute(dv, mv, 'counts', msg)

    def assertVariantsEquals(self, dvs, mvs, msg):
        self.assertEqual(len(dvs), len(mvs), "{}: len: {}, {}".
                         format(msg, len(dvs), len(mvs)))
        dvs.sort(key=lambda v: (v.location, v.familyId))
        mvs.sort(key=lambda v: (v.location, v.familyId))

        for i, dv in enumerate(dvs):
            mv = mvs[i]
            self.assertVariantEquals(dv, mv,
                                     "variant {} doesn't match".format(i))

    def assertSummaryVariantsEquals(self, dvs, mvs, msg):
        self.assertEqual(len(dvs), len(mvs), "{}: len: {}, {}".
                         format(msg, len(dvs), len(mvs)))
        dvs.sort(key=lambda v: (v.location,))
        mvs.sort(key=lambda v: (v.location,))

        for i, dv in enumerate(dvs):
            mv = mvs[i]
            self.assertSummaryVariantEquals(
                dv, mv,
                "summary variant {} doesn't match".format(i))
