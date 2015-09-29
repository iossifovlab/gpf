'''
Created on Sep 29, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from rest_framework import status


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


class Test(APITestCase):

    def test_single_phenotype(self):
        data = {
                "denovoStudies": "ALL WHOLE EXOME",
                "effectTypes": "Frame-shift,Nonsense,Splice-site",
                "gender": "female,male",
                "geneSet": "denovo",
                "geneTerm": "LGDs.Recurrent",
                "gene_set_phenotype": "congenital heart disease",
                "genes": "Gene Sets",
                "phenoType": "autism,congenital heart disease,epilepsy,intelectual disability,schizophrenia,unaffected",
                "studyType": "TG,WE",
                "variantTypes": "del,ins,sub",
        }

        url = '/api/we_query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(4 + 1, count_iterable(response.streaming_content))

    def test_double_phenotype(self):
        data = {
                "denovoStudies": "ALL WHOLE EXOME",
                "effectTypes": "Frame-shift,Nonsense,Splice-site",
                "gender": "female,male",
                "geneSet": "denovo",
                "geneTerm": "LGDs.Recurrent",
                "gene_set_phenotype": "congenital heart disease,epilepsy",
                "genes": "Gene Sets",
                "phenoType": "autism,congenital heart disease,epilepsy,intelectual disability,schizophrenia,unaffected",
                "studyType": "TG,WE",
                "variantTypes": "del,ins,sub",
        }

        url = '/api/we_query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(8 + 1, count_iterable(response.streaming_content))


if __name__ == "__main__":
    unittest.main()
