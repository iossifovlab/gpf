from rest_framework import status
from rest_framework.test import APITestCase

from studies.studies import get_denovo_studies_names, \
    get_transmitted_studies_names
from VariantAnnotation import get_effect_types
from query_variants import get_variant_types, get_child_types


class ApiTest(APITestCase):

    def test_query_variants(self):
        url = '/api/query_variants'
        data = {"denovoStudies": ["DalyWE2012"],
                "transmittedStudies": ["wig683"],
                "inChild": "sibF",
                "effectTypes": "frame-shift",
                "variantTypes": "del",
                "ultraRareOnly": "True"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.streaming_content

        data.next()
        for row in data:
            self.assertIn('del', row)
            self.assertIn('frame-shift', row)
            self.assertIn('sibF', row)

    def test_gene_set_response(self):
        # Test simple with gene_set only provided
        url_gs = '/api/gene_set_list2?gene_set=main'
        response = self.client.get(url_gs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(response.data), 31)

        # Test with no gene_set provided
        url_no_gs = '/api/gene_set_list2'
        response = self.client.get(url_no_gs)
        self.assertEqual(response.data, {})

        # Test with filter but not looking by key, nor desc
        url_filter_empty = "/api/gene_set_list2?gene_set=main&filter=mike&" \
            "key=false&desc=false"
        response = self.client.get(url_filter_empty)
        self.assertEqual(response.data, {})

        # Test with filter looking by key
        url_filter_key = '/api/gene_set_list2?gene_set=main&filter=mat&' \
            'key=true&desc=false'
        response = self.client.get(url_filter_key)
        self.assertNotEqual(response.data, {})
        for g in response.data:
            self.assertIn('mat', g.lower())

        #         # Test with filter looking by desc
        #         url_filter_desc = '/api/gene_set_list2?gene_set=main&' \
        #             'filter=mat&key=false&desc=true'
        #         response = self.client.get(url_filter_desc)
        #         self.assertNotEqual(response.data, {})
        #         for g in response.data:
        #             self.assertIn('mat', response.data[g]['desc'].lower())

        #         # Test with gene name
        #         url_with_gn = '/api/gene_set_list2?gene_set=main&' \
        #             'gene_name=PDS'
        #         response = self.client.get(url_with_gn)
        #         self.assertNotEqual(response.data, {})

        # Test with wrong gene name
        url_with_wrong_gn = '/api/gene_set_list2?gene_set=main&gene_name=foo'
        response = self.client.get(url_with_wrong_gn)
        self.assertEqual(response.data, {})

        # Test page count attr
        url_page_count = '/api/gene_set_list2?gene_set=main&page_count=5'
        response = self.client.get(url_page_count)
        self.assertEqual(len(response.data), 5)

        # Test page count with wrong attr
        url_page_count = '/api/gene_set_list2?gene_set=main&page_count=foo'
        response = self.client.get(url_page_count)
        self.assertEqual(len(response.data), 14)

        url_page_count = '/api/gene_set_list2?gene_set=main&page_count=-10'
        response = self.client.get(url_page_count)
        self.assertEqual(len(response.data), 14)

    def test_child_type_list(self):
        response = self.client.get('/api/child_types')
        self.assertEqual(response.data, {'child_types': get_child_types()})

    def test_variant_types_list(self):
        response = self.client.get('/api/variant_types')
        self.assertEqual(response.data, {'variant_types': get_variant_types()})

    def test_get_effect_types(self):
        response = self.client.get('/api/effect_types')
        eff = ['All'] + get_effect_types(types=False, groups=True) + \
            get_effect_types(types=True, groups=False)
        self.assertEqual(response.data, {"effect_types": eff})

    def test_transmitted_studies_list(self):
        response = self.client.get('/api/transmitted_studies')
        self.assertEqual(
            response.data,
            {"transmitted_studies": get_transmitted_studies_names()})

    def test_report_studies(self):
        response = self.client.get('/api/report_studies')
        data = {"report_studies": get_denovo_studies_names() +
                get_transmitted_studies_names()}
        self.assertEqual(response.data, data)

    def test_denovo_studies_list(self):
        data = get_denovo_studies_names()
        response = self.client.get('/api/denovo_studies')
        self.assertEqual(response.data, {'denovo_studies': data})

    def test_families_get(self):
        response = self.client.get('/api/families/DalyWE2012')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['study'], 'DalyWE2012')

    def test_families_get_filter(self):
        response = self.client.get('/api/families/DalyWE2012?filter=AU')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['study'], 'DalyWE2012')
        for family in data['families']:
            self.assertTrue(family.startswith('AU'))
