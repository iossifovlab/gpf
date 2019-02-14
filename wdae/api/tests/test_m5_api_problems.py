# import unittest
import logging
import urllib
import urlparse
# import itertools

# from VariantAnnotation import get_effect_types, get_effect_types_set
# from VariantsDB import mat2Str

from DAE import vDB
from query_prepare import prepare_ssc_filter
# from query_variants_bak import dae_query_variants, pedigree_data

from rest_framework import status
from rest_framework.test import APITestCase
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import pytest

LOGGER = logging.getLogger(__name__)


@pytest.mark.skip(reason="no way of currently testing this")
class RecurrentLGDsGenesTests(APITestCase):

    def test_load_gene_set(self):
        geneTerms = vDB.get_denovo_sets("AUTISM")
        LOGGER.info("gene terms: %s", geneTerms.t2G.keys())
        self.assertEqual(15, len(geneTerms.t2G.keys()))

    def test_rec_lgds_count(self):
        geneTerms = vDB.get_denovo_sets("AUTISM")
        LOGGER.info("gene terms: %s", geneTerms.t2G.keys())
        LOGGER.info("rec lgds: %s", geneTerms.t2G["prb.LoF.Recurrent"])
        LOGGER.info("rec lgds: %s",
                    len(geneTerms.t2G["prb.LoF.Recurrent"].keys()))
        self.assertEqual(45, len(geneTerms.t2G["prb.LoF.Recurrent"].keys()))


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


@pytest.mark.skip(reason="no way of currently testing this")
class PhenotypeFilterTests(APITestCase):

    def test_phenotype_BTN1A1_BTNL2(self):
        data = {
            "geneSyms": "BTN1A1, BTNL2",
            "denovoStudies": "ALL WHOLE EXOME",
        }
        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        LOGGER.info("result: %s", response)
        for num, it in enumerate(response.streaming_content):
            LOGGER.info("line: %s: %s", num, it)

        LOGGER.info("len: %s", num)
        self.assertEqual(3, num)

    def test_phenotype_BTN1A1_BTNL2_schizophrenia(self):
        data = {
            "geneSyms": "BTN1A1, BTNL2",
            "denovoStudies": "ALL WHOLE EXOME",
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
            "denovoStudies": "ALL WHOLE EXOME",
        }

        url = '/api/query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(11, count_iterable(response.streaming_content))

    def test_phenotype_ATRX_SPEG_unaffected(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
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
            "denovoStudies": "ALL WHOLE EXOME",
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
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism,schizophrenia,unaffected",
            "effectTypes": "Nonsense,Frame-shift,Splice-site,"
            "Missense,No-frame-shift,noStart,noEnd,"
            "Synonymous,Non coding,Intron,Intergenic,3'-UTR,5'-UTR"
        }

        url = '/api/query_variants'

        response = self.client.post(
            url, urllib.urlencode(data),
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(10, count_iterable(response.streaming_content))

    def test_ATRX_SPEG_schizophrenia_autisim_unaffected_urlencoded(self):
        data = "genes=Gene+Symbols&geneSet=main&geneTerm=&" \
            "geneSyms=ATRX%2C+SPEG&geneRegionType=on&geneRegion=&" \
            "denovoStudies=ALL+WHOLE+EXOME&transmittedStudies=none&" \
            "rarity=ultraRare&phenoType=autism&phenoType=schizophrenia&" \
            "phenoType=unaffected&gender=male&gender=female&" \
            "variantTypes=sub&variantTypes=ins&variantTypes=del&" \
            "effectTypes=Nonsense&effectTypes=Frame-shift&" \
            "effectTypes=Splice-site&effectTypes=Missense&" \
            "effectTypes=No-frame-shift&effectTypes=noStart&" \
            "effectTypes=noEnd&effectTypes=Synonymous&" \
            "effectTypes=Non+coding&effectTypes=Intron&" \
            "effectTypes=Intergenic&effectTypes=3%27-UTR&" \
            "effectTypes=5%27-UTR&families=all&familyIds=&" \
            "familyRace=All&familyVerbalIqLo=&familyVerbalIqHi=&" \
            "familyQuadTrio=All&familyPrbGender=All&familySibGender=All"

        LOGGER.error("urldecoded: %s", urlparse.parse_qs(data))
        url = '/api/query_variants'

        response = self.client.post(
            url, data,
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(10, count_iterable(response.streaming_content))


@pytest.mark.skip(reason="no way of currently testing this")
class PrepareSSCFilterTests(APITestCase):

    def test_present_in_parent_neither(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "transmittedStudies": "w1202s766e611",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected",
            "presentInParent": 'neither',
            "gender": "male",
        }

        res = prepare_ssc_filter(data)

        self.assertEqual('None', res['transmittedStudies'])

    def test_present_in_child_neither(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "transmittedStudies": "w1202s766e611",
            "presentInChild": "neither",
            "presentInParent": 'neither',
            "gender": "male",
        }

        res = prepare_ssc_filter(data)
        self.assertEqual('None', res['denovoStudies'])

    def test_pheno_type_removed(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "transmittedStudies": "w1202s766e611",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected",
            "presentInParent": 'neither',
            "gender": "male",
            "phenoType": "autism",
        }

        res = prepare_ssc_filter(data)

        self.assertFalse('phenoType' in res)


@pytest.mark.skip(reason="no way of currently testing this")
class SSCPresentInParentTests(BaseAuthenticatedUserTest):

    def test_present_in_child_autism_only(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
            # "phenoType": "autism",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])

    def test_present_in_child_unaffected_only(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "unaffected only",
            "gender": "male,female",
            # "phenoType": "autism",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual('1', response.data['count'])

    def test_present_in_parent_all(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A,WRAP73,VWA5B1",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected,neither",
            "presentInParent":
            "mother only,father only,mother and father,neither",
            "gender": "male,female",
            "rarity": "ultraRare",
            "transmittedStudies": "w1202s766e611",
            "variantTypes": "sub,ins,del,CNV",
        }

        url = '/api/ssc_query_variants_preview'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('19', response.data['count'])

    def test_ssc_phenotype_CACNA1S(self):
        data = {
            "geneSyms": "CACNA1S",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "rarity": "ultraRare",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected,neither",
            "presentInParent":
            'mother only,father only,mother and father,neither',
        }
        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('203', response.data['count'])

    def test_rec_lgds_preview(self):
        data = {
            'geneRegionType': 'on',
            'familyIds': '',
            'genes': 'Gene Sets',
            'families': 'all',
            'geneSyms': '',
            'familyVerbalIqLo': '',
            'gene_set_phenotype': 'autism',
            'familySibGender': 'All',
            'rarity': 'ultraRare',
            'familyRace': 'All',
            'effectTypes': 'nonsense,frame-shift,splice-site',
            'familyQuadTrio': 'All',
            'presentInChild': 'autism only,autism and unaffected',
            'variantTypes': 'sub,ins,del,CNV',
            'gender': 'male,female',
            'geneTerm': 'LGDs.Recurrent',
            'presentInParent': 'neither',
            'familyVerbalIqHi': '',
            'geneRegion': '',
            'geneSet': 'denovo',
            'familyPrbGender': 'All'
        }

        url = '/api/ssc_query_variants_preview'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('85', response.data['count'])

    def test_present_in_child_all(self):
        self.client.login(email='admin@example.com', password='secret')

        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected",
            "gender": "male,female",
            # "phenoType": "autism",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual('5', response.data['count'])

    def test_present_in_parent_father(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A,WRAP73,VWA5B1",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected,neither",
            "gender": "male,female",
            "rarity": "ultraRare",
            "transmittedStudies": "w1202s766e611",
            "variantTypes": "sub,ins,del,CNV",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('5', response.data['count'])

    def test_ssc_phenotype_CCDC171(self):
        data = {
            "geneSyms": "CCDC171",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "rarity": "ultraRare",
            "presentInChild":
            "autism only,unaffected only,autism and unaffected,neither",
            "presentInParent":
            'mother only,father only,mother and father,neither',
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('148', response.data['count'])

    def test_present_in_child_autism_only_parent_father(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A,WRAP73,VWA5B1",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
            "rarity": "ultraRare",
            "transmittedStudies": "w1202s766e611",
            "variantTypes": "sub,ins,del,CNV",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('2', response.data['count'])

    def test_present_in_child_autism_and_unaffected(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism and unaffected",
            "gender": "male,female",
            # "phenoType": "autism",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # LOGGER.info("result data: %s", response.data)
        self.assertEqual('2', response.data['count'])


@pytest.mark.skip(reason="no way of currently testing this")
class SSCPresentInChildDownloadTests(BaseAuthenticatedUserTest):

    def test_rec_lgds_download(self):
        data = {
            'geneRegionType': 'on',
            'familyIds': '',
            'genes': 'Gene Sets',
            'families': 'all',
            'geneSyms': '',
            'familyVerbalIqLo': '',
            'gene_set_phenotype': 'autism',
            'familySibGender': 'All',
            'rarity': 'ultraRare',
            'familyRace': 'All',
            'effectTypes': 'nonsense,frame-shift,splice-site',
            'familyQuadTrio': 'All',
            'presentInChild': 'autism only,autism and unaffected',
            'variantTypes': 'sub,ins,del,CNV',
            'gender': 'male,female',
            'geneTerm': 'LGDs.Recurrent',
            'presentInParent': 'neither',
            'familyVerbalIqHi': '',
            'geneRegion': '',
            'geneSet': 'denovo',
            'familyPrbGender': 'All'
        }

        url = '/api/ssc_query_variants'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(87, count_iterable(response.streaming_content))

    def test_rec_lgds_download_urlencoded(self):
        data = 'genes=Gene+Sets&geneSet=denovo&' \
            'gene_set_phenotype=autism&geneTerm=LGDs.Recurrent&' \
            'geneSyms=&geneRegionType=on&geneRegion=&' \
            'presentInChild=autism+only&' \
            'presentInChild=autism+and+unaffected& ' \
            'presentInParent=neither&gender=male&gender=female&' \
            'variantTypes=sub&variantTypes=ins&variantTypes=del&' \
            'variantTypes=CNV&effectTypes=Nonsense&' \
            'effectTypes=Frame-shift&effectTypes=Splice-site&' \
            'rarity=ultraRare&families=all&familyIds=&familyRace=All&' \
            'familyVerbalIqLo=&familyVerbalIqHi=&familyQuadTrio=All&' \
            'familyPrbGender=All&familySibGender=All'

        LOGGER.info("urldecoded: %s", urlparse.parse_qs(data))
        url = '/api/ssc_query_variants'

        response = self.client.post(
            url, data,
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(87, count_iterable(response.streaming_content))
