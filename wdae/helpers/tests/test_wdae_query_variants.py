'''
Created on Apr 25, 2016

@author: lubo
'''
import unittest
from helpers.dae_query import prepare_query_dict


class Test(unittest.TestCase):

    def test_unicode_unbreakable_space(self):
        data = {
            # @IgnorePep8
            u'effectTypes': u'Nonsense,Frame-shift,Splice-site,Missense,No-frame-shift,noStart,noEnd',
            u'gender': u'male,female',
            u'gene_set_phenotype': u'',
            u'geneRegion': u'',
            u'genes': u'Gene Symbols',
            u'geneSet': u'',
            u'geneSyms':
            u'''ACTL6A 
ACTL6B\xa0
ARID4A\xa0
ARID5B
BCL11A
BRPF1
CHD3
CHD4
EPC2 
HDAC4
HDAC6
HDAC9
ING1 
KAT5
KAT7 
KAT8
MSL2 
NCOR2 
RCOR1 
SMARCC1
SMARCC2
SMARCD1 
TBL1X 
TBL1XR1''',
            u'geneTerm': u'',
            u'geneTermFilter': u'',
            u'geneWeight': u'',
            u'geneWeightMax': u'',
            u'geneWeightMin': u'',
            u'phenoType': u'autism,congenital heart disease,epilepsy,intellectual disability,schizophrenia,unaffected',
            u'studyType': u'WE,TG',
            u'variantTypes': u'sub,ins,del'
        }
        res = prepare_query_dict(data)
        self.assertIsNotNone(res)

if __name__ == "__main__":
    unittest.main()
