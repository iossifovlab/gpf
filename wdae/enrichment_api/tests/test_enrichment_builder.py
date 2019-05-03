'''
Created on Feb 17, 2017

@author: lubo
'''

from rest_framework.test import APITestCase
from enrichment_api.views import EnrichmentModelsMixin
from datasets.config import DatasetsConfig
from enrichment_api.enrichment_builder import EnrichmentBuilder
from datasets.datasets_factory import DatasetsFactory
from gene.gene_set_collections import GeneSetsCollections
from enrichment_api.enrichment_serializer import EnrichmentSerializer


class Test(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        model = EnrichmentModelsMixin().get_enrichment_model({})
        config = DatasetsConfig()
        factory = DatasetsFactory(config)
        dataset = factory.get_dataset('SD_TEST')
        gscs = GeneSetsCollections()
        gsc = gscs.get_gene_sets_collection('main')

        gene_set = gsc.get_gene_set('chromatin modifiers')

        builder = EnrichmentBuilder(dataset, model, gene_set['syms'])
        results = builder.build()
        serializer = EnrichmentSerializer(results)
        cls.res = serializer.serialize()

    def test_enrichment_builder(self):
        self.assertIsNotNone(self.res)

    def test_autism_lgds_all(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        # self.assertEquals(546, res['LGDs']['all']['count'])
        self.assertEquals(551, res['LGDs']['all']['count'])
        # self.assertEquals(36, res['LGDs']['all']['overlapped'])
        self.assertEquals(37, res['LGDs']['all']['overlapped'])

    def test_autism_missense_all(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertEquals(2581, res['missense']['all']['count'])
        self.assertEquals(95, res['missense']['all']['overlapped'])

    def test_autism_synonymous_all(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertEquals(1117, res['synonymous']['all']['count'])
        self.assertEquals(35, res['synonymous']['all']['overlapped'])

    def test_autism_lgds_rec(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertEquals(39, res['LGDs']['rec']['count'])
        self.assertEquals(9, res['LGDs']['rec']['overlapped'])

    def test_autism_missense_rec(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertEquals(386, res['missense']['rec']['count'])
        self.assertEquals(20, res['missense']['rec']['overlapped'])

    def test_autism_synonymous_rec(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertEquals(76, res['synonymous']['rec']['count'])
        self.assertEquals(4, res['synonymous']['rec']['overlapped'])

    def test_filter_hints_lgds_all(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertIn('countFilter', res['LGDs']['all'])
        count_filter = res['LGDs']['all']['countFilter']
        print(count_filter)
        assert set(count_filter['effectTypes']) == \
            set(['Frame-shift', 'Nonsense', 'Splice-site',
                 'No-frame-shift-newStop'])
        self.assertIn('overlapFilter', res['LGDs']['all'])
        overlap_filter = res['LGDs']['all']['overlapFilter']
        print(overlap_filter)
        assert set(overlap_filter['effectTypes']) == \
            set(['Frame-shift', 'Nonsense', 'Splice-site',
                 'No-frame-shift-newStop'])

    def test_filter_hints_lgds_all_gender(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertIn('countFilter', res['LGDs']['all'])
        count_filter = res['LGDs']['all']['countFilter']
        print(count_filter)
        assert set(count_filter['gender']) == \
            set(['male', 'female', 'unspecified'])

        self.assertIn('overlapFilter', res['LGDs']['all'])
        overlap_filter = res['LGDs']['all']['overlapFilter']
        print(overlap_filter)
        assert set(overlap_filter['gender']) == \
            set(['male', 'female', 'unspecified'])

    def test_filter_hints_lgds_rec_gender(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertIn('countFilter', res['LGDs']['rec'])
        count_filter = res['LGDs']['rec']['countFilter']
        print(count_filter)
        assert set(count_filter['gender']) == \
            set(['male', 'female'])

        self.assertIn('overlapFilter', res['LGDs']['rec'])
        overlap_filter = res['LGDs']['rec']['overlapFilter']
        print(overlap_filter)
        assert set(overlap_filter['gender']) == \
            set(['male', 'female'])

    def test_filter_hints_lgds_male_gender(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertIn('countFilter', res['LGDs']['male'])
        count_filter = res['LGDs']['male']['countFilter']
        print(count_filter)
        assert set(count_filter['gender']) == \
            set(['male'])

        self.assertIn('overlapFilter', res['LGDs']['male'])
        overlap_filter = res['LGDs']['male']['overlapFilter']
        print(overlap_filter)
        assert set(overlap_filter['gender']) == \
            set(['male'])

    def test_filter_hints_lgds_female_gender(self):
        res = self.res[0]
        self.assertEquals('autism', res['selector'])

        self.assertIn('countFilter', res['LGDs']['female'])
        count_filter = res['LGDs']['female']['countFilter']
        print(count_filter)
        assert set(count_filter['gender']) == \
            set(['female'])
