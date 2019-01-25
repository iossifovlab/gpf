'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

# make sure env variables are set correctly
import findspark; findspark.init()  # noqa this needs to be the first import

from builtins import range
from io import StringIO
import os
import shutil
import tempfile
import time

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
from ..vcf.annotate_variant_details import VcfVariantDetailsAnnotator

from ..thrift.parquet_io import save_ped_df_to_parquet,\
    VariantsParquetWriter

from ..thrift.raw_thrift import ThriftFamilyVariants
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
def default_genome():
    from DAE import genomesDB
    genome = genomesDB.get_genome()  # @UndefinedVariable
    return genome


@pytest.fixture(scope='session')
def default_gene_models():
    from DAE import genomesDB
    gene_models = genomesDB.get_gene_models()  # @UndefinedVariable
    return gene_models


@pytest.fixture(scope='session')
def allele_freq_annotator():
    return VcfAlleleFrequencyAnnotator()


@pytest.fixture(scope='session')
def variant_details_annotator():
    return VcfVariantDetailsAnnotator()


@pytest.fixture(scope='session')
def testing_thriftserver(request):
    from impala.dbapi import connect

    spark_home = os.environ.get("SPARK_HOME")
    assert spark_home is not None

    thrift_host = os.getenv("THRIFTSERVER_HOST", "127.0.0.1")
    thrift_port = int(os.getenv("THRIFTSERVER_PORT", 10000))

    def thrift_connect(retries=200):
        for count in range(retries + 1):
            try:
                time.sleep(2.0)
                print("trying to connect to thrift server: try={}".format(
                    count + 1))
                conn = connect(host=thrift_host, port=thrift_port,
                               auth_mechanism='PLAIN')
                return conn
            except Exception as ex:
                print("connect to thriftserver failed:", ex)
        return None

    conn = thrift_connect(3)
    if conn is not None:
        return conn

    start_cmd = "{}/sbin/start-thriftserver.sh " \
        "--hiveconf hive.server2.thrift.port={}".format(
            spark_home, thrift_port)

    print("starting thrift command: ", start_cmd)
    os.system(start_cmd)

    return thrift_connect()


@pytest.fixture
def temp_dirname(request):
    dirname = tempfile.mkdtemp(suffix='_data', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture
def temp_filename(request):
    dirname = tempfile.mkdtemp(suffix='_eff', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    output = os.path.join(
        dirname,
        'annotation.tmp'
    )
    return output


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


@pytest.fixture(scope='session')
def variants_vcf(default_genome, default_gene_models):
    def builder(path):
        from ..vcf.builder import variants_builder

        a_path = relative_to_this_test_folder(path)
        fvars = variants_builder(
            a_path, genome=default_genome, gene_models=default_gene_models,
            force_reannotate=True)
        return fvars
    return builder


@pytest.fixture(scope='session')
def variants_thrift(parquet_variants, testing_thriftserver):
    def builder(path):
        parquet_conf = parquet_variants(path)
        return ThriftFamilyVariants(
            config=parquet_conf,
            thrift_connection=testing_thriftserver)
    return builder


@pytest.fixture(scope='session')
def parquet_variants(request, variants_vcf):
    dirname = tempfile.mkdtemp(suffix='_data', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)
    request.addfinalizer(fin)

    def builder(path):
        basename = os.path.basename(path)
        fulldirname = os.path.join(dirname, basename)

        if Configure.parquet_prefix_exists(fulldirname):
            return Configure.from_prefix_parquet(fulldirname).parquet

        if not os.path.exists(fulldirname):
            os.mkdir(fulldirname)
        conf = Configure.from_prefix_parquet(fulldirname).parquet

        fvars = variants_vcf(path)

        assert not fvars.is_empty()

        save_ped_df_to_parquet(fvars.ped_df, conf.pedigree)

        variants_builder = VariantsParquetWriter(
            fvars.full_variants_iterator())
        variants_builder.save_variants_to_parquet(
            summary_filename=conf.summary_variant,
            family_filename=conf.family_variant,
            effect_gene_filename=conf.effect_gene_variant,
            member_filename=conf.member_variant,
            batch_size=2)

        return conf

    return builder


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
