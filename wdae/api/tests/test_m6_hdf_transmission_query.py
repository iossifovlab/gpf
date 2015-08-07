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
        where = tq.build_freq_where()
        self.assertTrue(' ( n_alt_alls == 1 ) ', where)

    def test_hdf_freq_default(self):
        tq = self.tquery
        where = tq.build_freq_where()
        self.assertTrue(' ( n_par_called > 600 )  &  ( alt_freq <= 5.0 ) ',
                        where)

    def test_hdf_freq_min_max(self):
        tq = self.tquery
        tq['max_alt_freq_prcnt'] = 15.0
        tq['min_alt_freq_prcnt'] = 1.0
        tq['min_parents_called'] = None
        where = tq.build_freq_where()
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

    def test_hdf_family_ids_where_single(self):
        tq = self.tquery
        tq['family_ids'] = ['ala', 'bala']
        where = tq.build_family_ids_where()
        self.assertIsNotNone(where)
        pattern = ' ( family_id == "ala" )  |  ( family_id == "bala" ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_parent_mom(self):
        tq = self.tquery
        tq['present_in_parent'] = ['mom']
        where = tq.build_present_in_parent_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_mom == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_parent_dad(self):
        tq = self.tquery
        tq['present_in_parent'] = ['dad']
        where = tq.build_present_in_parent_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_dad == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_parent_mom_and_dad(self):
        tq = self.tquery
        tq['present_in_parent'] = ['mom', 'dad']
        where = tq.build_present_in_parent_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_mom == 1 )  &  ( in_dad == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_child_prb(self):
        tq = self.tquery
        tq['present_in_child'] = ['prb']
        where = tq.build_present_in_child_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_prb == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_child_sib(self):
        tq = self.tquery
        tq['present_in_child'] = ['sib']
        where = tq.build_present_in_child_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_sib == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_child_prb_and_sib(self):
        tq = self.tquery
        tq['present_in_child'] = ['prb', 'sib']
        where = tq.build_present_in_child_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_prb == 1 )  &  ( in_sib == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_child_gender_male(self):
        tq = self.tquery
        tq['present_in_child_gender'] = ['M']
        where = tq.build_present_in_child_gender_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_prb_gender == 0 ) | ( in_sib_gender == 0 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_child_gender_female(self):
        tq = self.tquery
        tq['present_in_child_gender'] = ['F']
        where = tq.build_present_in_child_gender_where()
        self.assertIsNotNone(where)
        pattern = ' ( in_prb_gender == 1 ) | ( in_sib_gender == 1 ) '
        self.assertEquals(pattern, where)

    def test_hdf_present_in_child_gender_male_or_female(self):
        tq = self.tquery
        tq['present_in_child_gender'] = ['F', 'M']
        where = tq.build_present_in_child_gender_where()
        self.assertIsNone(where)

    def test_hdf_is_effect_query_gene_syms(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ']
        self.assertTrue(tq.is_effect_query())

    def test_hdf_is_effect_query_effect_types(self):
        tq = self.tquery
        tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
        self.assertTrue(tq.is_effect_query())

    def test_hdf_is_effect_query_both(self):
        tq = self.tquery
        tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
        tq['gene_syms'] = ['POGZ']
        self.assertTrue(tq.is_effect_query())

    def test_hdf_is_effect_query_not(self):
        tq = self.tquery
        self.assertFalse(tq.is_effect_query())

        tq['family_ids'] = ['ala', 'bala']
        self.assertFalse(tq.is_effect_query())



if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
