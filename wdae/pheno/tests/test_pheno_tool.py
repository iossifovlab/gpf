'''
Created on Aug 9, 2016

@author: lubo
'''
import unittest
from pheno import pheno_request, pheno_tool


class Test(unittest.TestCase):

    def test_non_verbal_iq_lgds(self):
        data = {
            u'phenoMeasure': u'non_verbal_iq',
            u'denovoStudies': u'ALL SSC',
            u'effectTypeGroups': u'LGDs',
            u'presentInParent': u'neither',
        }

        req = pheno_request.Request(data)
        self.assertIsNotNone(req)

        tool = pheno_tool.PhenoTool(req)
        self.assertIsNotNone(tool)

        families_with_variants = tool.build_families_with_variants()
        self.assertIsNotNone(families_with_variants)

        for fid in families_with_variants['LGDs'].keys():
            self.assertIn(fid, req.families)
