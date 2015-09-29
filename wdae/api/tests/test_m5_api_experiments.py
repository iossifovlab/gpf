import unittest
import logging
import urllib
import itertools

from VariantAnnotation import get_effect_types, get_effect_types_set
# from VariantsDB import mat2Str

# from DAE import vDB
from api.query.query_prepare import prepare_denovo_studies
from api.query.query_variants import dae_query_variants  # , pedigree_data

from rest_framework import status
from rest_framework.test import APITestCase

LOGGER = logging.getLogger(__name__)


class EffectTypesFiltersTests(APITestCase):
    def test_effect_types(self):
        LOGGER.info("All: %s", get_effect_types(types=True, groups=True))
        LOGGER.info("Groups: %s", get_effect_types(types=False, groups=True))
        LOGGER.info("Play: %s", get_effect_types(types=True, groups=False))
        LOGGER.info("LoF: %s", get_effect_types_set('LoF'))
        LOGGER.info("LGD: %s", get_effect_types_set('LGDs'))
        coding = get_effect_types_set('coding')
        LOGGER.info("coding: %s", coding)

    def test_effect_types_all(self):
        data = {"effectFilter": "All"}
        url = '/api/effect_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        LOGGER.info("result data: %s", response.data)

    def test_effect_types_bad_request(self):
        data = {"effectFilter": "strangefilter"}
        url = '/api/effect_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        LOGGER.info("result data: %s", response.data)

    def test_effect_types_non_coding(self):
        data = {"effectFilter": "noncoding"}
        url = '/api/effect_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        LOGGER.info("result data: %s", response.data)

    def test_effect_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms": "SCNN1D",
                "denovoStudies": "IossifovWE2014",
                "variantTypes": "All",
                "effectTypes": "Nonsense,Missense",
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        LOGGER.info("result: %s", result)
        self.assertEqual('2', result['count'])

    def test_effect_filters_ARHGAP30_nonsense(self):
        url = '/api/query_variants_preview'

#         data = {"geneSyms":"ARHGAP30",
#                 "denovoStudies":'ALL WHOLE EXOME',
#                 "variantTypes":"All",
#                 "effectTypes":  "nonsense,frame-shift,splice-site",
#         }

        data = {"geneSyms": "ARHGAP30",
                "denovoStudies": 'ALL WHOLE EXOME',
                "variantTypes": "All",
                "effectTypes": "nonsense",
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        self.assertEqual('1', result['count'])

    def test_effect_filters_ARHGAP30_nonsense_frame_shift(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms": "ARHGAP30",
                "denovoStudies": 'ALL WHOLE EXOME',
                "variantTypes": "All",
                "effectTypes": "nonsense,frame-shift,splice-site",
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        self.assertEqual('1', result['count'])


class VariantTypesFiltersTests(APITestCase):

    def test_variant_types_whole_exome(self):
        data = {"variantFilter": "WHOLE EXOME"}
        url = '/api/variant_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        LOGGER.info("result data: %s", response.data)

    def test_variant_types_ssc(self):
        data = {"variantFilter": "SSC"}
        url = '/api/variant_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        LOGGER.info("result data: %s", response.data)

    def test_variant_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms": "CHD2",
                "denovoStudies": "IossifovWE2014",
                "variantTypes": "All",
                "effectTypes": "LGDs"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        self.assertEqual('3', result['count'])

        data = {"geneSyms": "CHD2",
                "denovoStudies": "IossifovWE2014",
                "variantTypes": "del",
                "effectTypes": "LGDs"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        self.assertEqual('1', result['count'])

        data = {"geneSyms": "CHD2",
                "denovoStudies": "IossifovWE2014",
                "variantTypes": "del,ins",
                "effectTypes": "LGDs"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        self.assertEqual('2', result['count'])

        data = {"geneSyms": "CHD2",
                "denovoStudies": "IossifovWE2014",
                "variantTypes": "del,ins,sub",
                "effectTypes": "LGDs"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        LOGGER.info("result: %s", result)
        self.assertEqual('3', result['count'])

    def test_variant_filters_cnv(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms": "DOC2A",
                "denovoStudies": "LevyCNV2011",
                "variantTypes": "CNV",
                "effectTypes": "All"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data

        self.assertEqual('10', result['count'])


class PhenotypeFiltersTests(APITestCase):

    def test_pheno_types_whole_exome(self):
        data = {"phenotypeFilter": "WHOLE EXOME"}
        url = '/api/pheno_types_filters?%s' % urllib.urlencode(data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_variant_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms": "CCDC171",
                "denovoStudies": "ALL WHOLE EXOME",
                "variantTypes": "All",
                "effectTypes": "All"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])

    def test_phenotype_filters(self):
        url = '/api/query_variants_preview'

        data = {"geneSyms": "CCDC171",
                "denovoStudies": "ALL WHOLE EXOME",
                "variantTypes": "All",
                "effectTypes": "All",
                'phenoType': 'autism',
                'gender': 'female,male',
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])


class VariantPedigreeTests(unittest.TestCase):
    def test_pedigree_CUL1(self):
        data = {
            "geneSyms": "CUL1",
            "denovoStudies": "ALL WHOLE EXOME",
        }

        dst = prepare_denovo_studies(data)
        self.assertFalse(dst is None)
        vsl = dae_query_variants(data)
        variants = itertools.chain(*vsl)

        for v in variants:

            for _m in v.memberInOrder:
                pass

    def test_pedigree_ALK(self):
        data = {
            "geneSyms": "ALK",
            "denovoStudies": "ALL WHOLE EXOME",
        }

        dst = prepare_denovo_studies(data)
        self.assertFalse(dst is None)
        vsl = dae_query_variants(data)
        variants = itertools.chain(*vsl)

        for _v in variants:
            pass


class PhenotypeFilterTests(APITestCase):
    def test_phenotype_BTN1A1_BTNL2(self):
        data = {
            "geneSyms": "BTN1A1, BTNL2",
            "denovoStudies": "ALL WHOLE EXOME",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])

    def test_phenotype_BTN1A1_BTNL2_schizophrenia(self):
        data = {
            "geneSyms": "BTN1A1, BTNL2",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "schizophrenia",
            "gender": "female,male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])

    def test_phenotype_ATRX_SPEG(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('8', response.data['count'])

    def test_phenotype_ATRX_SPEG_unaffected(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "unaffected",
            "gender": "female,male"
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('3', response.data['count'])

    def test_phenotype_ATRX_SPEG_schizophrenia(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "schizophrenia",
            "gender": "female,male"
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])

    def test_phenotype_ATRX_SPEG_schizophrenia_autisim_unaffected(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism,schizophrenia,unaffected",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('8', response.data['count'])


class GenderFilterTests(APITestCase):
    def test_gender_ATRX_SPEG(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('8', response.data['count'])

    def test_gender_ATRX_SPEG_female(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism,schizophrenia,unaffected",
            "gender": "female",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('3', response.data['count'])

    def test_gender_ATRX_SPEG_male(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism,schizophrenia,unaffected",
            "gender": "male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('5', response.data['count'])

    def test_gender_ATRX_SPEG_autism_male(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('4', response.data['count'])

    def test_gender_ATRX_SPEG_autism_female(self):
        data = {
            "geneSyms": "ATRX, SPEG",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "female",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('0', response.data['count'])


class SSCPhenotypeFilterTests(APITestCase):
    def test_ssc_phenotype_CCDC171(self):
        data = {
            "geneSyms": "CCDC171",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "rarity": "ultraRare",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('147', response.data['count'])

    def test_ssc_phenotype_CACNA1S(self):
        data = {
            "geneSyms": "CACNA1S",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "w1202s766e611",
            "rarity": "ultraRare",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('203', response.data['count'])


class SSCPresentInChildTests(APITestCase):
    def test_present_in_child_all(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only,unaffected only,"
            "autism and unaffected",
            'presentInParent': 'neither',
            "gender": "male,female",
            'inChild': "None",

            # "phenoType": "autism",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for _c, _r in enumerate(response.data['rows']):
            pass
        self.assertEqual('5', response.data['count'])

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

        url = '/api/query_variants_preview'

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

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])

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

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])


class SSCPresentInParentTests(APITestCase):
    def test_present_in_parent_all(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A,WRAP73,VWA5B1",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only,unaffected only,"
            "autism and unaffected,neither",
            "presentInParent": "mother only,father only,"
            "mother and father,neither",
            "gender": "male,female",
            # "phenoType": "autism",
            "rarity": "ultraRare",
            "transmittedStudies": "w1202s766e611",
            "variantTypes": "sub,ins,del,CNV",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('19', response.data['count'])

    def test_present_in_parent_father(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A,WRAP73,VWA5B1",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            # "denovoStudies": "ALL SSC",
            "presentInChild": "autism only,unaffected only,"
            "autism and unaffected,neither",
            "presentInParent": "father only",
            "gender": "male,female",
            # "phenoType": "autism",
            "rarity": "ultraRare",
            "transmittedStudies": "w1202s766e611",
            "variantTypes": "sub,ins,del,CNV",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('9', response.data['count'])

    def test_present_in_child_autism_only_parent_father(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A,WRAP73,VWA5B1",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            # "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "presentInParent": "father only",
            "gender": "male,female",
            # "phenoType": "autism",
            "rarity": "ultraRare",
            "transmittedStudies": "w1202s766e611",
            "variantTypes": "sub,ins,del,CNV",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('4', response.data['count'])


class PhenotypeFilterTestsSRI(APITestCase):

    def test_phenotype_SRI(self):

        data = {
            "geneSyms": "SRI",
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism,unaffected",
            "gender": "male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])

        pedigree_data = response.data['rows'][0][26]
        self.assertEqual(
            '["schizophrenia", [["mom", "F", 0], '
            '["dad", "M", 0], ["sib", "M", 1]]]',
            pedigree_data)


class SSCPresentInChildGenderTests(APITestCase):
    def test_present_in_child_male_all(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only,unaffected only,"
            "autism and unaffected",
            "gender": "male",
            # "phenoType": "autism",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('3', response.data['count'])

    def test_present_in_child_male_autism_only(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male",
            # "phenoType": "autism",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('0', response.data['count'])

    def test_present_in_child_male_unaffected_only(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "unaffected only",
            "gender": "male",
            # "phenoType": "autism",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])

    def test_present_in_child_male_autism_and_unaffected(self):
        data = {
            "geneSyms": "JAKMIP1,OR4C11,OSBPL,OTUD4,PAX5,PHF21A",
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism and unaffected",
            "gender": "male",
            # "phenoType": "autism",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])
