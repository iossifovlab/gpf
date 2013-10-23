import unittest

from DAE import *
from api.dae_query import *

class StudiesTests(unittest.TestCase):
    
    def test_denovo_studies_empty(self):
        dsl=prepare_denovo_studies({'denovoStudies':[]})
        self.assertTrue(not dsl)
        
        dsl=prepare_denovo_studies({})
        self.assertTrue(not dsl)

    def test_denovo_studies_single(self):
        dsl=prepare_denovo_studies({'denovoStudies':["DalyWE2012"]})
        self.assertEquals(len(dsl),1)
        self.assertEqual(dsl[0].name, "DalyWE2012")
        
        dsl=prepare_denovo_studies({'denovoStudies':["EichlerTG2012"]})
        self.assertEquals(len(dsl),1)
        self.assertEqual(dsl[0].name, "EichlerTG2012")
        
    
    def test_denovo_studies_double(self):
        dsl=prepare_denovo_studies({'denovoStudies':["DalyWE2012","EichlerTG2012"]})
        self.assertEquals(len(dsl),2)
        
        self.assertEqual(dsl[0].name, "DalyWE2012")
        self.assertEqual(dsl[1].name, "EichlerTG2012")
        

class InChildTests(unittest.TestCase):
    def test_inchild_empty(self):
        self.assertIsNone(prepare_inchild({}))
        self.assertIsNone(prepare_inchild({'inChild':None}))
        self.assertIsNone(prepare_inchild({'inChild':'None'}))
        self.assertIsNone(prepare_inchild({'inChild':'All'}))
        self.assertIsNone(prepare_inchild({'inChild':'none'}))

        
    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild({'inChild':'prb'}),'prb')
        self.assertEqual(prepare_inchild({'inChild':'sib'}),'sib')
        self.assertEqual(prepare_inchild({'inChild':'prbM'}),'prbM')
        self.assertEqual(prepare_inchild({'inChild':'sibF'}),'sibF')
        self.assertEqual(prepare_inchild({'inChild':'sibM'}),'sibM')
        self.assertEqual(prepare_inchild({'inChild':'prbF'}),'prbF')

    def test_inchild_not_correct(self):
        self.assertIsNone(prepare_inchild({'inChild':'prbMsibM'}))
        self.assertIsNone(prepare_inchild({'inChild':'prbMsibF'}))
        self.assertIsNone(prepare_inchild({'inChild':'ala-bala'}))

class EffectTypesTests(unittest.TestCase):
    ALL="LGDs,CNVs,nonsynonymous,CNV-,CNV+,frame-shift,intron,no-frame-shift-new-stop,synonymous,nonsense,no-frame-shift,missense,3'UTR,5'UTR,splice-site"
    def test_effect_types_all(self):
        self.assertEqual(prepare_effect_types({'effectTypes':'All'}),self.ALL)
        
    def test_effect_types_none(self):
        self.assertIsNone(prepare_effect_types({}))
        self.assertIsNone(prepare_effect_types({'effectTypes':None}))
        self.assertIsNone(prepare_effect_types({'effectTypes':'None'}))
        self.assertIsNone(prepare_effect_types({'effectTypes':'none'}))

    def test_effect_types_correct(self):
        self.assertEqual(prepare_effect_types({'effectTypes':'LGDs'}),'LGDs')
        self.assertEqual(prepare_effect_types({'effectTypes':'CNVs'}),'CNVs')
        self.assertEqual(prepare_effect_types({'effectTypes':'nonsynonymous'}),'nonsynonymous')
        self.assertEqual(prepare_effect_types({'effectTypes':'CNV-'}),'CNV-')
        self.assertEqual(prepare_effect_types({'effectTypes':'CNV+'}),'CNV+')
        self.assertEqual(prepare_effect_types({'effectTypes':'frame-shift'}),'frame-shift')
        self.assertEqual(prepare_effect_types({'effectTypes':'intron'}),'intron')
        self.assertEqual(prepare_effect_types({'effectTypes':'no-frame-shift-new-stop'}),'no-frame-shift-new-stop')
        self.assertEqual(prepare_effect_types({'effectTypes':'synonymous'}),'synonymous')
        self.assertEqual(prepare_effect_types({'effectTypes':'nonsense'}),'nonsense')
        self.assertEqual(prepare_effect_types({'effectTypes':'no-frame-shift'}),'no-frame-shift')
        self.assertEqual(prepare_effect_types({'effectTypes':'missense'}),'missense')
        self.assertEqual(prepare_effect_types({'effectTypes':"3'UTR"}),"3'UTR")
        self.assertEqual(prepare_effect_types({'effectTypes':"5'UTR"}),"5'UTR")
        self.assertEqual(prepare_effect_types({'effectTypes':"splice-site"}),"splice-site")

    def test_effect_types_not_correct(self):
        self.assertEqual(prepare_effect_types({'effectTypes':'ala-bala'}),self.ALL)


class VariantTypesTests(unittest.TestCase):
    
    def test_variant_types_all(self):
        self.assertIsNone(prepare_variant_types({'variantTypes':'All'}))

    def test_variant_type_none(self):
        self.assertIsNone(prepare_variant_types({}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'None'}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'none'}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : None}))

    def test_variant_types_correct(self):
        self.assertEqual(prepare_variant_types({'variantTypes':'CNV+'}),'CNV+')
        self.assertEqual(prepare_variant_types({'variantTypes':'CNV-'}),'CNV-')
        self.assertEqual(prepare_variant_types({'variantTypes':'snv'}),'snv')
        self.assertEqual(prepare_variant_types({'variantTypes':'ins'}),'ins')
        self.assertEqual(prepare_variant_types({'variantTypes':'del'}),'del')

    def test_variant_type_not_correct(self):
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'ala'}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'bala'}))



class FamilesTests(unittest.TestCase):
    
    def test_families_empty(self):
        self.assertIsNone(prepare_family_ids({}))

    def test_families_none(self):
        self.assertIsNone(prepare_family_ids({'familiesList' : 'None'}))
        self.assertIsNone(prepare_family_ids({'familiesList' : 'none'}))
        self.assertIsNone(prepare_family_ids({'familiesList' : 'All'}))
        self.assertIsNone(prepare_family_ids({'familiesList' : 'all'}))
        self.assertIsNone(prepare_family_ids({'familiesList' : None}))
        self.assertIsNone(prepare_family_ids({'familiesList' : 15}))

    def test_families_string(self):
        self.assertListEqual(prepare_family_ids({'familiesList' : '111'}),['111'])
        self.assertListEqual(prepare_family_ids({'familiesList' : '111,222'}),['111','222'])
        self.assertListEqual(prepare_family_ids({'familiesList' : '111 , 222'}),['111','222'])
        self.assertListEqual(prepare_family_ids({'familiesList' : '111    ,    222'}),['111','222'])
        self.assertListEqual(prepare_family_ids({'familiesList' : '111     ,    222,'}),['111','222'])

    def test_fimiles_list(self):
        self.assertListEqual(prepare_family_ids({'familiesList' : ['111']}),['111'])
        self.assertListEqual(prepare_family_ids({'familiesList' : ['111','222']}),['111','222'])
    

class GenSymsTests(unittest.TestCase):
    
    def test_gen_syms_empty(self):
        self.assertIsNone(prepare_gene_syms({}))

    def test_gen_syms_none(self):
        self.assertIsNone(prepare_gene_syms({'geneSym' : ''}))
        self.assertIsNone(prepare_gene_syms({'geneSym' : '    '}))
        self.assertIsNone(prepare_gene_syms({'geneSym' : None}))
    
    def test_gen_syms_correct_string(self):
        self.assertSetEqual(prepare_gene_syms({'geneSym' : 'CDH1'}),set(['CDH1']))
        self.assertSetEqual(prepare_gene_syms({'geneSym' : 'CDH1,SCO2'}),set(['CDH1','SCO2']))
        self.assertSetEqual(prepare_gene_syms({'geneSym' : 'CDH1      ,      SCO2'}),set(['CDH1','SCO2']))
        self.assertSetEqual(prepare_gene_syms({'geneSym' : 'CDH1      ,      SCO2  ,   '}),set(['CDH1','SCO2']))

if __name__ == '__main__':
    unittest.main()
    
