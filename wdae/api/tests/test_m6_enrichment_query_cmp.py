'''
Created on Jun 12, 2015

@author: lubo
'''
import unittest
from api.enrichment import background
from query_prepare import prepare_transmitted_studies
from api.enrichment.enrichment import build_transmitted_background
from api.deprecated.bg_loader import preload_background
from api.enrichment.enrichment_query import enrichment_results_by_phenotype,\
    enrichment_prepare
from api.enrichment.results import EnrichmentTestBuilder, EnrichmentTest
from api.enrichment.views import EnrichmentView
from DAE import vDB, get_gene_sets_symNS
from api.enrichment.config import PRB_TESTS_SPECS
from api.enrichment.denovo_counters import DenovoEventsCounter,\
    filter_denovo_studies_by_phenotype


class EnrichmentQuery(object):

    def __init__(self, query, background):
        self.query = query
        self.background = background

    def build(self, background, denovo_counter):
        self.enrichment = EnrichmentTestBuilder()
        self.enrichment.build(background, denovo_counter)

    def calc(self):
        print(self.query)
        dsts = self.query['denovoStudies']
        gene_syms = self.query['geneSyms']
        self.result = self.enrichment.calc(dsts, gene_syms)

        return self.result


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.background = background.SynonymousBackground()
        cls.background.precompute()

        transmitted = prepare_transmitted_studies(
            {"transmittedStudies": 'w1202s766e611'})

        builders = [
            (build_transmitted_background,
             transmitted,
             'enrichment_background')
        ]

        preload_background(builders)

    def test_autism_enrichment_result(self):
        self.dsts = vDB.get_studies('ALL WHOLE EXOME')
        gt = get_gene_sets_symNS('main')
        self.gene_syms = gt.t2G['FMRP-Darnell'].keys()

        spec = PRB_TESTS_SPECS[1]
        eres = EnrichmentTest.make_variant_events_enrichment(
            spec, self.background, DenovoEventsCounter)
        adsts = filter_denovo_studies_by_phenotype(self.dsts, 'autism')
        res = eres.calc(adsts, self.gene_syms)
        self.assertTrue(res)

    FULL_QUERY = {'denovoStudies': 'ALL WHOLE EXOME',
                  'geneSet': 'main',
                  'geneTerm': 'FMRP-Darnell'}

    def test_all_query(self):
        data = EnrichmentView.enrichment_prepare(self.FULL_QUERY)
        print("data: {}".format(data))
        enrichment_query = EnrichmentQuery(data, self.background)

        enrichment_query.build(self.background, DenovoEventsCounter)

        res = enrichment_query.calc()

        res_old = enrichment_results_by_phenotype(
            **enrichment_prepare(self.FULL_QUERY))

        for phenotype in res.keys():
            er = res[phenotype]
            er_old = res_old[phenotype]
            for r, r_old in zip(er, er_old):

                self.assertEquals(r.count, r_old['count'])
                self.assertAlmostEquals(r.expected, float(r_old['expected']),
                                        places=4)
                self.assertAlmostEquals(r.p_val, float(r_old['p_val']),
                                        places=4)
                self.assertEquals(r.total, r_old['overlap'])


if __name__ == "__main__":
    unittest.main()
