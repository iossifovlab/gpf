import unittest
import logging
# import itertools

from DAE import vDB
from query_prepare import prepare_denovo_studies
from api.enrichment.enrichment_query import enrichment_prepare, \
    enrichment_results_by_phenotype
from api.enrichment.enrichment import build_transmitted_background

from bg_loader import preload_background

from api.enrichment.enrichment import collect_prb_enrichment_variants_by_phenotype, \
    collect_sib_enrichment_variants_by_phenotype, \
    filter_prb_enrichment_variants_by_phenotype, \
    filter_sib_enrichment_variants_by_phenotype, \
    build_enrichment_variants_genes_dict_by_phenotype, \
    count_gene_set_enrichment_by_phenotype, \
    count_background
    
logger = logging.getLogger(__name__)


class EnrichmentBasicTest(unittest.TestCase):
    def test_collect_prb_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }

        dsts = prepare_denovo_studies(data)
        res = collect_prb_enrichment_variants_by_phenotype(dsts)

        # logger.info("collected variants: %s", res)
        # logger.info("collected variants phenotypes: %s", len(res.keys()))
        self.assertEqual(5, len(res.keys()))

    def test_collect_prb_variants_by_phenotype_autism(self):
        data = {
            "denovoStudies":"AUTISM",
        }

        dsts = prepare_denovo_studies(data)
        res = collect_prb_enrichment_variants_by_phenotype(dsts)

        # logger.info("collected variants: %s", res)
        # logger.info("collected variants phenotypes: %s", len(res.keys()))
        self.assertEqual(1, len(res.keys()))

    def test_collect_sib_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }

        dsts = prepare_denovo_studies(data)
        res = collect_sib_enrichment_variants_by_phenotype(dsts)

        # logger.info("collected SIB variants: %s", res)
        self.assertEqual(12, len(res))

    def test_filter_prb_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }

        dsts = prepare_denovo_studies(data)
        evars = collect_prb_enrichment_variants_by_phenotype(dsts)

        res = filter_prb_enrichment_variants_by_phenotype(evars)
        # logger.info("filtered enrichment variants phenotypes: %s", res.keys())
        self.assertEqual(5, len(res.keys()))
        for _phenotype, fevars in res.items():
            self.assertEqual(12, len(fevars))


    def test_filter_prb_variants_by_phenotype_autism(self):
        data = {
            "denovoStudies":"AUTISM",
        }

        dsts = prepare_denovo_studies(data)
        evars = collect_prb_enrichment_variants_by_phenotype(dsts)

        res = filter_prb_enrichment_variants_by_phenotype(evars)
        # logger.info("filtered enrichment variants phenotypes: %s", res.keys())
        self.assertEqual(1, len(res.keys()))

        for _phenotype, fevars in res.items():
            self.assertEqual(12, len(fevars))

    def test_filter_sib_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }

        dsts = prepare_denovo_studies(data)
        evars = collect_sib_enrichment_variants_by_phenotype(dsts)
        res = filter_sib_enrichment_variants_by_phenotype(evars)

        self.assertEqual(12, len(res))

    def test_build_enrichment_variants_genes_dict(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }

        dsts = prepare_denovo_studies(data)
        genes_dict_by_pheno = build_enrichment_variants_genes_dict_by_phenotype(dsts)
        logger.info("genes dict by pheno: %s", sorted(genes_dict_by_pheno.keys()))


    def test_count_gene_set_enrichment_by_phenotype_whole_exome(self):
        data = enrichment_prepare({
            "denovoStudies":"ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
        })

        dsts = data['denovoStudies']
        gene_syms_set = data['geneSyms']

        genes_dict_by_pheno = build_enrichment_variants_genes_dict_by_phenotype(
                dsts)
        # logger.info("genes dict by pheno: %s", sorted(genes_dict_by_pheno.keys()))

        count_res = count_gene_set_enrichment_by_phenotype(genes_dict_by_pheno, gene_syms_set)
        # logger.info("count res: %s", count_res)
        # logger.info("count res keys: %s", sorted(count_res.keys()))
        self.assertEqual(5 + 1, len(count_res.keys()))

    def test_count_gene_set_enrichment_by_phenotype_whole_exome_FMR1_targets(self):
        data = enrichment_prepare({
            "denovoStudies":"ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'FMR1-targets',
            'geneSet': 'main',
        })

        dsts = data['denovoStudies']
        gene_syms_set = data['geneSyms']

        genes_dict_by_pheno = build_enrichment_variants_genes_dict_by_phenotype(
                dsts)
        
        # logger.info("genes dict by pheno: %s", sorted(genes_dict_by_pheno.keys()))

        count_res = count_gene_set_enrichment_by_phenotype(genes_dict_by_pheno, gene_syms_set)
        # logger.info("count res: %s", count_res)
        # logger.info("count res keys: %s", sorted(count_res.keys()))
        self.assertEqual(5 + 1, len(count_res.keys()))


class EnrichmentWithBackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tsts = vDB.get_study('w1202s766e611')
        builders = [(build_transmitted_background,
                     [cls.tsts],
                     'enrichment_background')]

        preload_background(builders)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_count_gene_set_enrichment_by_phenotype_whole_exome(self):
        data = enrichment_prepare({
            "denovoStudies":"ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
        })

        gene_syms_set = data['geneSyms']

        background_count = count_background(gene_syms_set)
        # logger.info("background_count: %s", background_count)
        self.assertEqual(6890, background_count.cnt)

#     def test_enrichment_test_by_phenotype_whole_exome(self):
#         data = enrichment_prepare({
#             "denovoStudies":"ALL WHOLE EXOME",
#             'geneSyms': '',
#             'geneStudy': '',
#             'transmittedStudies': 'w1202s766e611',
#             'geneTerm': 'ChromatinModifiers',
#             'geneSet': 'main',
#         })
# 
#         gene_syms_set = data['geneSyms']
#         dsts = data['denovoStudies']
# 
#         count_res_by_pheno, totals_by_pheno, genes_dict_by_pheno = \
#             enrichment_test_by_phenotype(dsts, gene_syms_set)
# 
#         # logger.info("count_res_by_pheno=%s", count_res_by_pheno)
#         # logger.info("totals_by_pheno=%s", totals_by_pheno)
#         # logger.info('autism rec lgds: %s', genes_dict_by_pheno['autism']['prb|Rec LGDs'])

#     def test_enrichment_results_by_phenotype_whole_exome(self):
#         data = enrichment_prepare({
#             "denovoStudies":"ALL WHOLE EXOME",
#             'geneSyms': '',
#             'geneStudy': '',
#             'transmittedStudies': 'w1202s766e611',
#             'geneTerm': 'ChromatinModifiers',
#             'geneSet': 'main',
#         })
#
#         res = enrichment_results_by_phenotype(**data)
#         logger.info("enrichment results by phenotype: %s", res)
#
#         import pprint
#         pprint.pprint(res)

    def test_enrichment_results_by_phenotype_whole_exome_FMR1_targets(self):
        data = enrichment_prepare({
            "denovoStudies":"ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'FMR1-targets',
            'geneSet': 'main',
        })

        res = enrichment_results_by_phenotype(**data)
        logger.info("enrichment results by phenotype: %s", res)

#         import pprint
#         pprint.pprint(res)
#         pprint.pprint(res['unaffected'][0])
        unaffected_rec_lgds=res['unaffected'][0]
        self.assertTrue(unaffected_rec_lgds.has_key('syms'))

    def test_enrichment_results_by_phenotype_rec_synonymous(self):
        data = enrichment_prepare({
            "denovoStudies":"ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'FMR1-targets',
            'geneSet': 'main',
        })
        print "geneSyms:", data['geneSyms']
        
        res = enrichment_results_by_phenotype(**data)
        # logger.info("enrichment results by phenotype: %s", res)

#         import pprint
#         pprint.pprint(res)
#         pprint.pprint(res['autism'][8])
        rec_synonymous=res['autism'][8]
        self.assertEquals(rec_synonymous['label'], 'Rec Synonymous')

    def test_enrichment_results_by_phenotype_rec_missense(self):
        data = enrichment_prepare({
            "denovoStudies":"ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'FMR1-targets',
            'geneSet': 'main',
        })

        res = enrichment_results_by_phenotype(**data)
        # logger.info("enrichment results by phenotype: %s", res)

        rec_synonymous=res['autism'][4]
        self.assertEquals(rec_synonymous['label'], 'Rec Missense')
