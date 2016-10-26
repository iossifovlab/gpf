'''
Created on Jun 15, 2015

@author: lubo
'''
from rest_framework import status
from rest_framework.test import APITestCase

from enrichment.views import EnrichmentView


class Test(APITestCase):

    def test_gene_set_prepare(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'chromatin modifiers',
            'geneSet': 'main',
        }
        view = EnrichmentView()
        view.data = EnrichmentView.enrichment_prepare(data)

        self.assertEquals('main', view.gene_set)
        self.assertEquals('chromatin modifiers', view.gene_term)

    def test_gene_syms_prepare(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': 'SCNN1D,MEGF6',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
        }
        view = EnrichmentView()
        view.data = EnrichmentView.enrichment_prepare(data)

        self.assertIsNone(view.gene_set)
        self.assertIsNone(view.gene_term)
        self.assertEquals(set(['SCNN1D', 'MEGF6']), set(view.gene_syms))

    def test_gene_set_serialize_common(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'chromatin modifiers',
            'geneSet': 'main',
        }
        view = EnrichmentView()
        view.data = EnrichmentView.enrichment_prepare(data)

        res = view.serialize_response_common_data()

        self.assertEquals('main', res['gs_id'])
        self.assertEquals('Gene Set: chromatin modifiers: Iossifov I., et al. '
                          'The contribution of de novo coding mutations to '
                          'autism spectrum disorder. Nature (2014)',
                          res['gs_desc'])
        self.assertEquals(428, res['gene_number'])

    def test_gene_syms_serialize(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': 'SCNN1D,MEGF6',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
        }
        view = EnrichmentView()
        view.data = EnrichmentView.enrichment_prepare(data)

        res = view.serialize_response_common_data()

        gene_list = ','.join(sorted(view.gene_syms))
        self.assertEquals(gene_list, res['gs_id'])
        self.assertEquals(gene_list, res['gs_desc'])
        self.assertEquals(2, res['gene_number'])

    def test_gene_set_calc_and_serialize(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'chromatin modifiers',
            'geneSet': 'main',
        }

        url = '/api/enrichment_test_by_phenotype'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
