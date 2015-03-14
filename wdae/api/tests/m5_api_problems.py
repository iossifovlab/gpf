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