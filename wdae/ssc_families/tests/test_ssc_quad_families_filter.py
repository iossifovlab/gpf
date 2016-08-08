'''
Created on Jul 7, 2016

@author: lubo
'''


import unittest
from ssc_families.ssc_filter import QuadFamiliesFilter, FamiliesGenderFilter
from api.default_ssc_study import get_ssc_denovo_studies
from ssc_families.ssc_families_precompute import SSCFamiliesPrecompute


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.quad_filter = QuadFamiliesFilter()
        self.gender_filter = FamiliesGenderFilter()

    def test_quad_siblings_count_IossifovWE2014(self):
        families = self.quad_filter.get_matching_families(
            study_type=None, study_name='IossifovWE2014')
        self.assertEquals(1902, len(families))

        male_siblings = self.gender_filter.filter_matching_siblings(
            families, 'M', study_type=None, study_name='IossifovWE2014')

        female_siblings = self.gender_filter.filter_matching_siblings(
            families, 'F', study_type=None, study_name='IossifovWE2014')

        self.assertEquals(1902, len(male_siblings) + len(female_siblings))

        mismatched_siblings = set(male_siblings) & \
            set(self.gender_filter.get_matching_siblings(
                'F', study_type=None, study_name='IossifovWE2014'))

        self.assertEquals(0, len(mismatched_siblings))

    def test_quad_probands_count_cnv(self):
        families = self.quad_filter.get_matching_families(
            study_type='cnv', study_name=None)
        self.assertEquals(2225, len(families))

        male_probands = self.gender_filter.filter_matching_probands(
            families, 'M', study_type='cnv', study_name=None)

        female_probands = self.gender_filter.filter_matching_probands(
            families, 'F', study_type='cnv', study_name=None)

        self.assertEquals(2225, len(male_probands) + len(female_probands))

        mismatched_probands = set(male_probands) & \
            set(self.gender_filter.get_matching_probands(
                'F', study_type='cnv', study_name=None))

        self.assertEquals(0, len(mismatched_probands))

    MIXED_SIBLINGS_GENDER = set([
        '11093', '11942', '11601', '11117', '11324', '11501', '11529',
        '11306', '11740', '11079', '11031', '11241', '12296', '12390',
        '11264', '11429', '12231', '11421', '11280', '12219', '11282',
        '12152', '11930', '11397', '12325', '11471', '11551', '11550',
        '11089', '12555', '11557', '11490', '11892', '11146', '11393',
        '11009', '11148', '11066', '12227', '11470', '11905', '11432',
        '11630', '12201'])

    def test_quad_siblings_count_cnv(self):

        families = set(
            self.quad_filter.get_matching_families(
                study_type='cnv', study_name=None))
        self.assertEquals(2225, len(families))

        self.assertEquals(0, len(self.MIXED_SIBLINGS_GENDER & families))

        male_siblings = set(
            self.gender_filter.filter_matching_siblings(
                families, 'M', study_type='cnv', study_name=None)) & families

        female_siblings = set(
            self.gender_filter.filter_matching_siblings(
                families, 'F', study_type='cnv', study_name=None)) & families

        # self.assertEquals(2351, len(male_siblings) + len(female_siblings))

        mismatched_siblings = set(male_siblings) & set(female_siblings)

        print(mismatched_siblings)
        cnv_studies = [st for st in get_ssc_denovo_studies()
                       if st.get_attr('study.type').lower() == 'cnv']
        for fid in mismatched_siblings:
            fams = []
            for st in cnv_studies:
                f = st.families[fid]
                f.study = st
                fams.append(f)

            self.assertEquals(2, len(fams))
            [f1, f2] = fams
            print("fid: {}; st: {}={}; st: {}={}".format(
                fid,
                f1.study.name, len(f1.memberInOrder),
                f2.study.name, len(f2.memberInOrder)))

        self.assertEquals(0, len(mismatched_siblings))

    def test_quad_probands_cnv(self):
        families = set(
            self.quad_filter.get_matching_families(
                study_type='cnv', study_name=None))
        self.assertEquals(2225, len(families))

        male_probands = set(
            self.gender_filter.filter_matching_probands(
                families, 'M', study_type='cnv', study_name=None)) & families

        female_probands = set(
            self.gender_filter.filter_matching_probands(
                families, 'F', study_type='cnv', study_name=None)) & families

        # self.assertEquals(2351, len(male_siblings) + len(female_siblings))

        mismatched_probands = set(male_probands) & set(female_probands)

        print(mismatched_probands)
        self.assertEquals(0, len(mismatched_probands))

    def test_quads_cnv(self):
        study_type = 'cnv'
        families = self.quad_filter.get_matching_families(
            study_type=study_type, study_name=None)
        self.assertEquals(2225, len(families))

        studies = [st for st in get_ssc_denovo_studies()
                   if st.get_attr('study.type').lower() == study_type]
        for st in studies:
            for fid in families:
                if fid not in st.families:
                    continue
                fam = st.families[fid]
                self.assertTrue(4, len(fam.memberInOrder))

        self.assertEquals(0, len(self.MIXED_SIBLINGS_GENDER & set(families)))

    def test_build_cnv_quads(self):
        precompute = SSCFamiliesPrecompute()
        study_type = 'cnv'
        studies = [st for st in get_ssc_denovo_studies()
                   if st.get_attr('study.type').lower() == study_type]

        quads, _nonquads = precompute._build_quads(studies)
        print(set(quads) & self.MIXED_SIBLINGS_GENDER)

        self.assertEquals(0, len(set(quads) & self.MIXED_SIBLINGS_GENDER))
