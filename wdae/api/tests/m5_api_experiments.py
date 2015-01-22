import unittest
import logging
import urllib

from VariantAnnotation import get_effect_types, get_effect_types_set

from rest_framework import status
from rest_framework.test import APITestCase

logger = logging.getLogger(__name__)

class M5ExperimentsTests(APITestCase):
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
                "effectTypes":["nonsense", "missense"]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('2', result['count'])


        data = {"geneSyms":"SCNN1D",
                "denovoStudies":"IossifovWE2014",
                "variantTypes":"All",
                "effectTypes":"nonsense,missense"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        logger.info("result: %s", result)
        self.assertEqual('2', result['count'])
        