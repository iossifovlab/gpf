'''
Created on Apr 3, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from enrichment.enrichment_builder import DenovoStudies, ChildrenStats
from datasets.datasets_factory import DatasetsFactory
from pprint import pprint


class Test(APITestCase):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()

        denovo_studies = DenovoStudies()
        cs_old = ChildrenStats()
        cls.ores = cs_old.build(denovo_studies)
        pprint(cls.ores)

        df = DatasetsFactory()
        dataset = df.get_dataset('SD')
        cls.res = dataset.enrichment_children_stats
        pprint(cls.res)

    def test_compare_denovo_studies(self):
        denovo_studies = DenovoStudies()
        sts = set([st.name for st in denovo_studies.studies
                   if 'WE' == st.get_attr('study.type')])
        pprint(sts)

        df = DatasetsFactory()
        dataset = df.get_dataset('SD')
        res = set([st.name for st in dataset.enrichment_denovo_studies])
        pprint(res)

        self.assertEquals(len(sts), len(res))

    def test_compare_autism_male(self):
        self.assertEquals(
            self.ores['autism']['M'],
            self.res['autism']['M'])

    def test_compare_autism_female(self):
        self.assertEquals(
            self.ores['autism']['F'],
            self.res['autism']['F'])

    def test_compare_congenital_heart_disease_male(self):
        self.assertEquals(
            self.ores['congenital heart disease']['M'],
            self.res['congenital heart disease']['M'])

    def test_compare_congenital_heart_disease_female(self):
        self.assertEquals(
            self.ores['congenital heart disease']['F'],
            self.res['congenital heart disease']['F'])

    def test_compare_unaffected_male(self):
        self.assertEquals(
            self.ores['unaffected']['M'],
            self.res['unaffected']['M'])

    def test_compare_unaffected_female(self):
        self.assertEquals(
            self.ores['unaffected']['F'],
            self.res['unaffected']['F'])

    def test_compare_epilepsy_male(self):
        self.assertEquals(
            self.ores['epilepsy']['M'],
            self.res['epilepsy']['M'])

    def test_compare_epilepsy_female(self):
        self.assertEquals(
            self.ores['epilepsy']['F'],
            self.res['epilepsy']['F'])

    def test_compare_schizophrenia_male(self):
        self.assertEquals(
            self.ores['schizophrenia']['M'],
            self.res['schizophrenia']['M'])

    def test_compare_schizophrenia_female(self):
        self.assertEquals(
            self.ores['schizophrenia']['F'],
            self.res['schizophrenia']['F'])
