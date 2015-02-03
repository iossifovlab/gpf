import unittest
import logging
import urllib
import itertools

from VariantAnnotation import get_effect_types, get_effect_types_set
from VariantsDB import mat2Str

from DAE import vDB
from query_prepare import prepare_denovo_studies
from query_variants import dae_query_variants, pedigree_data

from rest_framework import status
from rest_framework.test import APITestCase

logger = logging.getLogger(__name__)

class EffectTypesFiltersTests(APITestCase):
    def test_effect_types(self):
        logger.info("All: %s", get_effect_types(types=True, groups=True))
        logger.info("Groups: %s", get_effect_types(types=False, groups=True))
        logger.info("Play: %s", get_effect_types(types=True, groups=False))
        logger.info("LoF: %s", get_effect_types_set('LoF'))
        logger.info("LGD: %s", get_effect_types_set('LGDs'))
        coding = get_effect_types_set('coding')
        logger.info("coding: %s", coding)

    def test_effect_types_all(self):
        data = {"effectFilter": "All"}
        url = '/api/effect_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)

    def test_effect_types_bad_request(self):
        data = {"effectFilter": "strangefilter"}
        url = '/api/effect_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        logger.info("result data: %s", response.data)

    def test_effect_types_non_coding(self):
        data = {"effectFilter": "noncoding"}
        url = '/api/effect_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)

    def test_effect_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms":"SCNN1D",
                "denovoStudies":"IossifovWE2014",
                "variantTypes":"All",
                "effectTypes": "nonsense,missense",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('2', result['count'])


    def test_effect_filters_ARHGAP30(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms":"ARHGAP30",
                "denovoStudies":'ALL WHOLE EXOME',
                "variantTypes":"All",
                "effectTypes":  "nonsense,frame-shift,splice-site",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('1', result['count'])
        
class VariantTypesFiltersTests(APITestCase):

    def test_variant_types_whole_exome(self):
        data = {"variantFilter": "WHOLE EXOME"}
        url = '/api/variant_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)

    def test_variant_types_ssc(self):
        data = {"variantFilter": "SSC"}
        url = '/api/variant_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)

    def test_variant_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms":"CHD2",
                "denovoStudies":"IossifovWE2014",
                "variantTypes": "All",
                "effectTypes": "LGDs"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('3', result['count'])

        data = {"geneSyms":"CHD2",
                "denovoStudies":"IossifovWE2014",
                "variantTypes": "del",
                "effectTypes": "LGDs"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('1', result['count'])

        data = {"geneSyms":"CHD2",
                "denovoStudies":"IossifovWE2014",
                "variantTypes": "del,ins",
                "effectTypes": "LGDs"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('2', result['count'])

        data = {"geneSyms":"CHD2",
                "denovoStudies":"IossifovWE2014",
                "variantTypes": "del,ins,sub",
                "effectTypes": "LGDs"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('3', result['count'])

    def test_variant_filters_cnv(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms":"DOC2A",
                "denovoStudies":"LevyCNV2011",
                "variantTypes": "CNV",
                "effectTypes": "All"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('10', result['count'])

class PhenotypeFiltersTests(APITestCase):

    def test_pheno_types_whole_exome(self):
        data = {"phenotypeFilter": "WHOLE EXOME"}
        url = '/api/pheno_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)

    def test_variant_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms":"CCDC171",
                "denovoStudies":"ALL WHOLE EXOME",
                "variantTypes": "All",
                "effectTypes": "All"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)
        self.assertEqual('2', response.data['count'])

    def test_phenotype_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms":"CCDC171",
                "denovoStudies":"ALL WHOLE EXOME",
                "variantTypes": "All",
                "effectTypes": "All",
                'phenoTypes': 'autism'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result data: %s", response.data)
        self.assertEqual('1', response.data['count'])

    # def test_phenotype_filters_with_transmitted(self):
    #     url = '/api/query_variants_preview'

    #     data = {"geneSyms":"CCDC171",
    #             "denovoStudies":"ALL WHOLE EXOME",
    #             'transmittedStudies': 'w1202s766e611',
    #             'rarity': 'ultraRare',
    #             "variantTypes": "All",
    #             "effectTypes": "All",
    #             'phenoTypes': 'autism'
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     logger.info("result data: %s", response.data)
    #     self.assertEqual('1', response.data['count'])

    # def test_phenotype_filters_ssc_with_transmitted(self):
    #     url = '/api/query_variants_preview'

    #     data = {"geneSyms":"CHD8,ARID1B,POGZ",
    #             "denovoStudies":"ALL SSC",
    #             'transmittedStudies': 'w1202s766e611',
    #             'rarity': 'ultraRare',
    #             "variantTypes": "All",
    #             "effectTypes": "All",
    #             'phenoTypes': 'unaffected'
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     logger.info("result data: %s", response.data)
    #     self.assertEqual('1', response.data['count'])




class VariantPedigreeTests(unittest.TestCase):
    def test_pedigree_CUL1(self):
        data = {
            "geneSyms": "CUL1",
            "denovoStudies":"ALL WHOLE EXOME",
        }

        
        dst = prepare_denovo_studies(data)
        self.assertFalse(dst is None)
        vsl = dae_query_variants(data)
        variants = itertools.chain(*vsl)
        
        for v in variants:
            logger.info("v.inChS=%s; v.bestSt=%s", v.inChS, mat2Str(v.bestSt))
            for m in v.memberInOrder:
                logger.info("m.role=%s; m.gender=%s; ", m.role, m.gender)

    def test_pedigree_ALK(self):
        data = {
            "geneSyms": "ALK",
            "denovoStudies":"ALL WHOLE EXOME",
        }

        
        dst = prepare_denovo_studies(data)
        self.assertFalse(dst is None)
        vsl = dae_query_variants(data)
        variants = itertools.chain(*vsl)
        
        for v in variants:
            logger.info("v.inChS=%s; v.bestSt=%s", v.inChS, mat2Str(v.bestSt))
            logger.info("pedigree=%s", pedigree_data(v))
            logger.info('v.popType=%s; v.atts=%s', v.popType, v.atts)
            logger.info('v.pedigree=%s', v.pedigree)