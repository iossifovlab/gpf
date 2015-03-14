import unittest
import logging
import urllib
import urlparse
import itertools

from VariantAnnotation import get_effect_types, get_effect_types_set
from VariantsDB import mat2Str

from DAE import vDB
from query_prepare import prepare_denovo_studies
from query_variants import dae_query_variants, pedigree_data

from rest_framework import status
from rest_framework.test import APITestCase

logger = logging.getLogger(__name__)

class RecurrentLGDsGenesTests(APITestCase):
    def test_load_gene_set(self):
        geneTerms = vDB.get_denovo_sets("AUTISM")
        logger.info("gene terms: %s", geneTerms.t2G.keys())
        self.assertEqual(15, len(geneTerms.t2G.keys()))

    def test_rec_lgds_count(self):
        geneTerms = vDB.get_denovo_sets("AUTISM")
        logger.info("gene terms: %s", geneTerms.t2G.keys())
        logger.info("rec lgds: %s", geneTerms.t2G["prb.LoF.Recurrent"])
        logger.info("rec lgds: %s", len(geneTerms.t2G["prb.LoF.Recurrent"].keys()))
        self.assertEqual(39, len(geneTerms.t2G["prb.LoF.Recurrent"].keys()))


def count_iterable(iterable):
    for num, it in enumerate(iterable):
        pass
    return num + 1
    
class PhenotypeFilterTests(APITestCase):
    def test_phenotype_BTN1A1_BTNL2(self):
        data = {
            "geneSyms": "BTN1A1, BTNL2",
            "denovoStudies":"ALL WHOLE EXOME",
        }

        
        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logger.info("result: %s", response)
        for num, it in enumerate(response.streaming_content):
            logger.info("line: %s: %s", num, it)

        logger.info("len: %s", num)
        self.assertEqual(3, num)

    def test_phenotype_BTN1A1_BTNL2_schizophrenia(self):
        data = {
            "geneSyms": "BTN1A1, BTNL2",
            "denovoStudies":"ALL WHOLE EXOME",
            "phenoType": "schizophrenia",
            "gender": "female,male",
        }

        
        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(3, count_iterable(response.streaming_content))

    def test_phenotype_ATRX_SPEG(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies":"ALL WHOLE EXOME",
        }

        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(10, count_iterable(response.streaming_content))

    def test_phenotype_ATRX_SPEG_unaffected(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies":"ALL WHOLE EXOME",
            "phenoType": "unaffected",
            "gender": "female,male"
        }

        
        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(5, count_iterable(response.streaming_content))

    def test_phenotype_ATRX_SPEG_schizophrenia(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies":"ALL WHOLE EXOME",
            "phenoType": "schizophrenia",
            "gender": "female,male"
        }

        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(3, count_iterable(response.streaming_content))

    def test_phenotype_ATRX_SPEG_schizophrenia_autisim_unaffected(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies":"ALL WHOLE EXOME",
            "phenoType": "autism,schizophrenia,unaffected",
            "effectType": "Nonsense,Frame-shift,Splice-site,Missense,Non-frame-shift,noStart,noEnd,Synonymous,Non coding,Intron,Intergenic,3'-UTR,5'-UTR"
        }
        # data = {
        #     'geneRegionType': 'on',
        #     'denovoStudies': 'ALL WHOLE EXOME',
        #     'families': 'all',
        #     'variantTypes': 'sub,ins,del',
        #     'geneSyms': 'ATRX, SPEG',
        #     'familyVerbalIqLo': '',
        #     'familyQuadTrio': 'All',
        #     'familyIds': '',
        #     'rarity': 'ultraRare',
        #     'familyRace': 'All',
        #     'effectTypes': 'nonsense,frame-shift,splice-site',
        #     'familySibGender': 'All',
        #     'geneRegion': '',
        #     'familyPrbGender': 'All',
        #     'phenoType': 'schizophrenia,autism,unaffected',
        #     'genes': 'Gene Symbols',
        #     'gender': 'male,female',
        #     'transmittedStudies': 'none',
        #     'familyVerbalIqHi': '',
        #     'geneTerm': '',
        #     'geneSet': 'main'
        # }

        url = '/api/query_variants'

        response = self.client.post(url, urllib.urlencode(data),
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(10, count_iterable(response.streaming_content))
        
    def test_phenotype_ATRX_SPEG_schizophrenia_autisim_unaffected_urlencoded(self):
        data = "genes=Gene+Symbols&geneSet=main&geneTerm=&geneSyms=ATRX%2C+SPEG&geneRegionType=on&geneRegion=&denovoStudies=ALL+WHOLE+EXOME&transmittedStudies=none&rarity=ultraRare&phenoType=autism&phenoType=schizophrenia&phenoType=unaffected&gender=male&gender=female&variantTypes=sub&variantTypes=ins&variantTypes=del&effectTypes=Nonsense&effectTypes=Frame-shift&effectTypes=Splice-site&effectTypes=Missense&effectTypes=Non-frame-shift&effectTypes=noStart&effectTypes=noEnd&effectTypes=Synonymous&effectTypes=Non+coding&effectTypes=Intron&effectTypes=Intergenic&effectTypes=3%27-UTR&effectTypes=5%27-UTR&families=all&familyIds=&familyRace=All&familyVerbalIqLo=&familyVerbalIqHi=&familyQuadTrio=All&familyPrbGender=All&familySibGender=All"
        logger.info("urldecoded: %s", urlparse.parse_qs(data))
        url = '/api/query_variants'

        response = self.client.post(url, data,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(10, count_iterable(response.streaming_content))
        
    # def test_phenotype_ATRX_SPEG_schizophrenia_autisim_unaffected_urlencoded_2(self):

    #     data = {
    #         # 'geneRegionType': ['on'],
    #         # 'families': ['all'],
    #         'denovoStudies': ['ALL WHOLE EXOME'],
    #         # 'gender': ['male', 'female'],
    #         # 'genes': ['Gene Symbols'],
    #         # 'rarity': ['ultraRare'],
    #         'effectTypes': ['Nonsense', 'Frame-shift', 'Splice-site'],
    #         # 'familySibGender': ['All'],
    #         # 'familyPrbGender': ['All'],
    #         'phenoType': ['schizophrenia','autism','unaffected'],
    #         'variantTypes': ['sub', 'ins', 'del'],
    #         # 'familyQuadTrio': ['All'],
    #         'transmittedStudies': ['none'],
    #         # 'familyRace': ['All'],
    #         # 'geneSet': ['main'],
    #         'geneSyms': ['ATRX,SPEG'],
    #     }
        
    #     url = '/api/query_variants'

    #     response = self.client.post(url, urllib.urlencode(data),
    #                                 content_type='application/x-www-form-urlencoded')

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(10, count_iterable(response.streaming_content))


    #     data = {'denovoStudies': "['ALL WHOLE EXOME']",
    #             'geneSyms': "['ATRX,SPEG']",
    #             'effectTypes': "['Nonsense', 'Frame-shift', 'Splice-site']",
    #             'phenoType': "['schizophrenia', 'autism', 'unaffected']",
    #             'variantTypes': "['sub', 'ins', 'del']",
    #             'transmittedStudies': "['none']"}