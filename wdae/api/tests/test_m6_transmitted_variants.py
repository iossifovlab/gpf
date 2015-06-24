'''
Created on Jun 24, 2015

@author: lubo
'''
import unittest
import numpy as np

from api.variants.transmitted_variants import read_summary_df, \
    regions_splitter, filter_summary_regions_df, filter_summary_parents_called,\
    filter_summary_alt_freq_prcnt, filter_summary_ultra_rare,\
    filter_summary_variant_types, filter_summary_gene_effect


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.df = read_summary_df('w1202s766e611')

    def setUp(self):
        pass


    def tearDown(self):
        pass



    def test_data_frame_loaded(self):
        self.assertEquals((1415355,16), self.df.shape)
        
    def test_data_frame_dtypes(self):
        self.assertEquals('|O8', self.df.chr.dtypes.str)
        
    def test_reions_matcher_simple(self):
        reg1 = "X:1000000-1001000"
        r = regions_splitter(reg1)
        self.assertEquals(1, len(r))
        [ri] = r
        self.assertEquals(ri[0], 'X')
        self.assertEquals(ri[1], 1000000)
        self.assertEquals(ri[2], 1001000)
        

    def test_reions_matcher_double(self):
        reg1 = "X:1000000-1001000, 1:1000-2000"
        r = regions_splitter(reg1)
        self.assertEquals(2, len(r))
        [r1,r2] = r
        self.assertEquals(r1[0], 'X')
        self.assertEquals(r1[1], 1000000)
        self.assertEquals(r1[2], 1001000)
        self.assertEquals(r2[0], '1')
        self.assertEquals(r2[1], 1000)
        self.assertEquals(r2[2], 2000)

    
    def test_reions_matcher_bad_begin_end(self):
        reg1 = "X:2000000-1001000"
        with self.assertRaises(ValueError):
            regions_splitter(reg1)

     
    def test_transmitted_filter_single_region(self):
        reg = "1:1000000-2000000"
        df = filter_summary_regions_df(self.df, reg)
        self.assertTrue(np.all(df.chr == '1'))
        self.assertTrue(np.all(df.position > 1000000))
        self.assertTrue(np.all(df.position < 2000000))
     

    def test_transmitted_filter_multi_region(self):
        reg = "1:1000000-2000000,2:0-1000000"
        df = filter_summary_regions_df(self.df, reg)
        df1 = df[df.chr == '1']
        df2 = df[df.chr == '2']
        self.assertTrue(np.all(df1.chr == '1'))
        self.assertTrue(np.all(df1.position > 1000000))
        self.assertTrue(np.all(df1.position < 2000000))

        self.assertTrue(np.all(df2.chr == '2'))
        self.assertTrue(np.all(df2.position > 0))
        self.assertTrue(np.all(df2.position < 1000000))
        
        self.assertTrue(len(df), len(df1)+len(df2))


    def test_transmitted_filter_parents_called(self):
        df = filter_summary_parents_called(self.df, minParentsCalled=200)
        self.assertTrue(np.all(df['all.nParCalled']>=200))

        
    def test_transmitted_filter_alt_freq_prcnt(self):
        df = filter_summary_alt_freq_prcnt(self.df, 
                                           minAltFreqPercnt=5, 
                                           maxAltFreqPrcnt=10)
        self.assertTrue(np.all(df['all.altFreq']>=5))
        self.assertTrue(np.all(df['all.altFreq']<=10))


    def test_transmitted_filter_ultra_rare(self):
        df = filter_summary_ultra_rare(self.df, ultraRareOnly=True)
        self.assertTrue(np.all(df['all.nAltAlls'] == 1))

    
    def test_transmitted_filter_variant_types(self):
        df = filter_summary_variant_types(self.df, set(['del']))
        self.assertTrue(np.all(np.vectorize(lambda v: v[0:3]=='del')(df.variant)))
        df = filter_summary_variant_types(self.df, set(['ins']))
        self.assertTrue(np.all(np.vectorize(lambda v: v[0:3]=='ins')(df.variant)))
        df = filter_summary_variant_types(self.df, set(['sub', 'del']))
        self.assertTrue(np.all(np.vectorize(lambda v: v[0:3]=='del' or v[0:3]=='sub')(df.variant)))
        
    def test_transmitted_filter_gene_syms(self):
        df = filter_summary_gene_effect(self.df, 
                                        effectTypes=None, 
                                        geneSyms=set(['POGZ']))
        self.assertEquals(156, len(df))
        vf = np.vectorize(lambda v: any([x['sym']=='POGZ' for x in v]))
        self.assertTrue(np.any(vf(df.effectGene)))
    
    def test_transmitted_filter_effect_types(self):
        df = filter_summary_gene_effect(self.df, 
                                        effectTypes=set(["3'UTR"]),
                                        geneSyms=None)
        self.assertEquals(31536, len(df))
        vf = np.vectorize(lambda v: any([x['eff']=="3'UTR" for x in v]))
        self.assertTrue(np.any(vf(df.effectGene)))
        
    def test_transmitted_filter_gene_syms_and_effect_types(self):
        df = filter_summary_gene_effect(self.df, 
                                        effectTypes=set(["3'UTR"]), 
                                        geneSyms=set(['POGZ']))
        self.assertEquals(1, len(df))
        vf = np.vectorize(lambda v: any([x['sym']=='POGZ' 
                                         and x['eff'] == "3'UTR" 
                                         for x in v]))
        self.assertTrue(np.any(vf(df.effectGene)))


    def test_transmitted_filter_gene_syms_and_effect_types_again(self):
        df = filter_summary_gene_effect(self.df, 
                                        effectTypes=set(["synonymous"]), 
                                        geneSyms=set(['POGZ']))
        self.assertEquals(50, len(df))
        vf = np.vectorize(lambda v: any([x['sym']=='POGZ' 
                                         and x['eff'] == "synonymous" 
                                         for x in v]))
        self.assertTrue(np.any(vf(df.effectGene)))



        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_filter_regions']
    unittest.main()