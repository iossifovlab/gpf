'''
Created on Aug 4, 2015

@author: lubo
'''
import unittest
from api.variants.hdf5_query import TransmissionQuery


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.tquery = TransmissionQuery('w1202s766e611')

    def setUp(self):
        pass

    def tearDown(self):
        self.tquery.clear_query()

    def test_hdf_filename(self):
        self.assertIsNotNone(self.tquery.hdf5_filename)
        self.assertIsNotNone(self.tquery.hdf5_fh)
        self.assertTrue(self.tquery.hdf5_fh.isopen)

    def test_hdf_ewhere_by_genes_single_sym(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ']
        where = tq.build_gene_syms_where()
        self.assertTrue(where)
        self.assertEquals(' ( symbol == "POGZ" ) ', where)

    def test_hdf_ewhere_by_genes_two_sym(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ', 'SCNN1D']
        where = tq.build_gene_syms_where()
        self.assertTrue(where)
        self.assertEquals(' ( symbol == "POGZ" )  |  ( symbol == "SCNN1D" ) ',
                          where)

    def test_hdf_freq_ultra_rare(self):
        tq = self.tquery
        tq['ultra_rare_only'] = True
        tq['min_parents_called'] = None
        where = tq.build_query_alt_freq()
        self.assertTrue(' ( n_alt_alls == 1 ) ', where)

    def test_hdf_freq_default(self):
        tq = self.tquery
        where = tq.build_query_alt_freq()
        self.assertTrue(' ( n_par_called > 600 )  &  ( alt_freq <= 5.0 ) ',
                        where)

    def test_hdf_freq_min_max(self):
        tq = self.tquery
        tq['max_alt_freq_prcnt'] = 15.0
        tq['min_alt_freq_prcnt'] = 1.0
        tq['min_parents_called'] = None
        where = tq.build_query_alt_freq()
        self.assertTrue(' ( alt_freq <= 15.0 )  &  ( alt_freq >= 1.0 )', where)

    def test_hdf_effect_query_gene_syms(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ', 'SCNN1D']
        where = tq.build_effect_query_where()
        pattern = ' (  ( symbol == "POGZ" )  |  ( symbol == "SCNN1D" )  )  & '
        pattern += ' (  ( n_par_called > 600 )  &  ( alt_freq <= 5.0 )  ) '
        self.assertEquals(pattern, where)

    def test_hdf_build_effect_type_query(self):
        tq = self.tquery
        tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
        where = tq.build_effect_types_where()
        self.assertIsNotNone(where)
        pattern = ' ( effect_type == 14 )  | '
        pattern += ' ( effect_type == 4 )  | '
        pattern += ' ( effect_type == 15 ) '

        self.assertEquals(pattern, where)

    def test_hdf_build_effect_type_query_single(self):
        tq = self.tquery
        tq['effect_types'] = ['nonsense']
        where = tq.build_effect_types_where()
        self.assertIsNotNone(where)
        pattern = ' ( effect_type == 14 ) '

        self.assertEquals(pattern, where)

    def test_hdf_build_variant_type_query_single(self):
        tq = self.tquery
        tq['variant_types'] = ['del']
        where = tq.build_variant_types_where()
        self.assertIsNotNone(where)
        pattern = ' ( variant_type == 0 ) '

        self.assertEquals(pattern, where)

    def test_hdf_build_variant_type_query_double(self):
        tq = self.tquery
        tq['variant_types'] = ['del', 'ins']
        where = tq.build_variant_types_where()
        self.assertIsNotNone(where)
        pattern = ' ( variant_type == 0 )  |  ( variant_type == 1 ) '

        self.assertEquals(pattern, where)

    def test_hdf_effect_query_combined(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ', 'SCNN1D']
        lgds = ['nonsense', 'frame-shift', 'splice-site']
        tq['effect_types'] = lgds
        tq['variant_types'] = ['ins', 'sub']
        vs = tq.execute_effect_query()
        self.assertIsNotNone(vs)
        self.assertEquals(2, len(vs))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
