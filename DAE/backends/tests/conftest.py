'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

# make sure env variables are set correctly
import findspark; findspark.init()  # noqa this needs to be the first import

from io import StringIO

import pytest

import logging

from pyspark.sql import SparkSession

from variants.family import Family, FamiliesBase
from variants.family_variant import FamilyVariant
from variants.variant import SummaryAllele, SummaryVariant

from ..attributes_query import PARSER as attributes_query_parser, \
    QueryTransformerMatcher
from ..attributes_query import \
    parser_with_ambiguity as attributes_query_parser_with_ambiguity
from ..configure import Configure

from ..vcf.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator

from ..thrift.raw_dae import RawDAE, RawDenovo

from .common_tests_helpers import relative_to_this_test_folder


def quiet_py4j():
    """ turn down spark logging for the test context """
    logger = logging.getLogger('py4j')
    logger.setLevel(logging.WARN)


@pytest.fixture(scope="session")
def spark(request):
    """ fixture for creating a spark context
    Args:
        request: pytest.FixtureRequest object
    """
    spark = SparkSession.\
        builder.\
        appName("pytest-pyspark-local-testing").\
        getOrCreate()

    request.addfinalizer(lambda: spark.stop())

    quiet_py4j()
    return spark


@pytest.fixture(scope="session")
def spark_context(spark):
    """ fixture for creating a spark context
    Args:
        request: pytest.FixtureRequest object
    """
    return spark.sparkContext


@pytest.fixture(scope='session')
def allele_freq_annotator():
    return VcfAlleleFrequencyAnnotator()


@pytest.fixture(scope='session')
def config_dae():
    def builder(path):
        fullpath = relative_to_this_test_folder(path)
        config = Configure.from_prefix_dae(fullpath)
        return config
    return builder


@pytest.fixture(scope='session')
def raw_dae(config_dae, default_genome):
    def builder(path, region=None):
        config = config_dae(path)
        dae = RawDAE(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            config.dae.family_filename,
            region=region,
            genome=default_genome,
            annotator=None)
        return dae
    return builder


@pytest.fixture(scope='session')
def config_denovo():
    def builder(path):
        fullpath = relative_to_this_test_folder(path)
        config = Configure.from_prefix_denovo(fullpath)
        return config
    return builder


@pytest.fixture(scope='session')
def raw_denovo(config_denovo, default_genome):
    def builder(path):
        config = config_denovo(path)
        denovo = RawDenovo(
            config.denovo.denovo_filename,
            config.denovo.family_filename,
            genome=default_genome,
            annotator=None)
        return denovo
    return builder


# @pytest.fixture(scope='session')
# def composite_annotator(
#         variant_details_annotator, allele_freq_annotator,
#         default_genome, default_gene_models):

#     effect_annotator = VcfVariantEffectsAnnotator(
#         genome=default_genome, gene_models=default_gene_models)

#     return AnnotatorComposite(annotators=[
#         variant_details_annotator,
#         effect_annotator,
#         allele_freq_annotator,
#     ])


@pytest.fixture
def variants_implementations(
        variants_vcf, variants_thrift):
    impls = {
        "variants_vcf": variants_vcf,
        "variants_thrift": variants_thrift,
    }
    return impls


@pytest.fixture
def variants_impl(variants_implementations):
    return lambda impl_name: variants_implementations[impl_name]


PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""


@pytest.fixture(scope='session')
def fam1():
    ped_df = FamiliesBase.load_pedigree_file(
        StringIO(PED1), sep=",")

    family = Family("f1", ped_df)
    assert len(family.trios) == 1
    return family


@pytest.fixture(scope='session')
def sv():
    return SummaryVariant([
        SummaryAllele("1", 11539, "T", None, 0, 0),
        SummaryAllele("1", 11539, "T", "TA", 0, 1),
        SummaryAllele("1", 11539, "T", "TG", 0, 2)
    ])


@pytest.fixture(scope='session')
def fv1(fam1, sv):
    def rfun(gt):
        return FamilyVariant(sv, fam1, gt)
    return rfun


@pytest.fixture()
def parser():
    return attributes_query_parser


@pytest.fixture()
def parser_with_ambiguity():
    return attributes_query_parser_with_ambiguity


@pytest.fixture()
def transformer_matcher():
    return QueryTransformerMatcher()


@pytest.fixture()
def transformer_matcher_class():
    return QueryTransformerMatcher
