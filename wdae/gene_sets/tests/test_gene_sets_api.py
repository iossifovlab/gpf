'''
Created on Feb 16, 2017

@author: lubo
'''


from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_gene_sets_collections(self):
        url = "/api/v3/gene_sets/collections"
        response = self.client.get(url,)
        self.assertEqual(200, response.status_code)

        data = response.data
        print(data)

        self.assertEquals(6, len(data))

        denovo = data[1]
        self.assertEquals('denovo', denovo['name'])
        self.assertEquals(6, len(denovo['types']))
