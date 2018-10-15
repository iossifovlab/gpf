'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

# make sure env variables are set correctly
import findspark  # this needs to be the first import
findspark.init()

from builtins import range
from io import StringIO
import os
import shutil
import tempfile
import time

import pytest

from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_details import VcfVariantDetailsAnnotator
from variants.annotate_variant_effects import \
    VcfVariantEffectsAnnotator
from variants.attributes_query import PARSER as attributes_query_parser, \
    QueryTransformerMatcher
from variants.attributes_query import \
    parser_with_ambiguity as attributes_query_parser_with_ambiguity
from variants.configure import Configure
from variants.family import Family, FamiliesBase
from variants.family_variant import FamilyVariant

from variants.parquet_io import family_variants_df, save_summary_to_parquet,\
    save_ped_df_to_parquet,\
    save_family_allele_df_to_parquet
from variants.raw_df import DfFamilyVariants
from variants.raw_parquet import ParquetFamilyVariants
from variants.raw_thrift import ThriftFamilyVariants
from variants.raw_vcf import RawFamilyVariants, \
    VariantFactory
from variants.variant import SummaryAllele, SummaryVariant
from variants.tests.common_tests_helpers import relative_to_this_test_folder
from variants.raw_dae import RawDAE, RawDenovo

import logging

from pyspark.sql import SparkSession


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
def effect_annotator(default_genome, default_gene_models):
    return VcfVariantEffectsAnnotator(
        genome=default_genome, gene_models=default_gene_models)


@pytest.fixture(scope='session')
def allele_freq_annotator():
    return VcfAlleleFrequencyAnnotator()


@pytest.fixture(scope='session')
def variant_details_annotator():
    return VcfVariantDetailsAnnotator()


@pytest.fixture(scope='session')
def composite_annotator(
        variant_details_annotator, effect_annotator, allele_freq_annotator):

    return AnnotatorComposite(annotators=[
        variant_details_annotator,
        effect_annotator,
        allele_freq_annotator,
    ])


@pytest.fixture(scope='session')
def testing_thriftserver(request):
    from impala.dbapi import connect

    spark_home = os.environ.get("SPARK_HOME")
    assert spark_home is not None

    thrift_host = os.getenv("THRIFTSERVER_HOST", "127.0.0.1")
    thrift_port = int(os.getenv("THRIFTSERVER_PORT", 10000))

    def thrift_connect(retries=10):
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

    conn = thrift_connect(1)
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


@pytest.fixture(scope='session')
def variants_vcf(composite_annotator):
    def builder(path):
        a_data = relative_to_this_test_folder(path)
        a_conf = Configure.from_prefix_vcf(a_data)
        fvars = RawFamilyVariants(
            a_conf, annotator=composite_annotator,
            variant_factory=VariantFactory)
        return fvars
    return builder


@pytest.fixture(scope='session')
def variants_df(variants_vcf):
    def builder(path):
        fvars = variants_vcf(path)
        summary_df = fvars.annot_df
        ped_df = fvars.ped_df
        allele_df = family_variants_df(
            fvars.query_variants(
                return_reference=True,
                return_unknown=True
            ))
        return DfFamilyVariants(ped_df, summary_df, allele_df)
    return builder


@pytest.fixture(scope='session')
def variants_thrift(parquet_variants, testing_thriftserver):
    def builder(path):
        pedigree, summary, allele = parquet_variants(path)
        config = Configure.from_dict({
            'parquet': {
                'pedigree': pedigree,
                'summary_variants': summary,
                'family_alleles': allele,
            }
        })
        return ThriftFamilyVariants(
            config=config,
            thrift_connection=testing_thriftserver)
    return builder


@pytest.fixture(scope='session')
def variants_parquet(parquet_variants):
    def builder(path):
        pedigree, summary, allele = parquet_variants(path)
        config = Configure.from_dict({
            'parquet': {
                'pedigree': pedigree,
                'summary_variants': summary,
                'family_alleles': allele,
            }
        })
        return ParquetFamilyVariants(config=config)
    return builder


@pytest.fixture(scope='session')
def parquet_variants(request, variants_df):
    dirname = tempfile.mkdtemp(suffix='_data', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)
    request.addfinalizer(fin)

    def builder(path):
        print("path:", path, os.path.basename(path))
        basename = os.path.basename(path)
        fulldirname = os.path.join(dirname, basename)
        summary_filename = os.path.join(
            fulldirname, "summary.parquet")
        allele_filename = os.path.join(
            fulldirname, "allele.parquet")
        pedigree_filename = os.path.join(
            fulldirname, "pedigree.parquet")

        if os.path.exists(summary_filename) and \
                os.path.exists(allele_filename) and \
                os.path.exists(pedigree_filename):
            return pedigree_filename, summary_filename, allele_filename

        if not os.path.exists(fulldirname):
            os.mkdir(fulldirname)

        assert os.path.exists(fulldirname)
        assert os.path.isdir(fulldirname)

        fvars = variants_df(path)
        save_summary_to_parquet(fvars.summary_df, summary_filename)
        save_family_allele_df_to_parquet(fvars.allele_df, allele_filename)
        save_ped_df_to_parquet(fvars.ped_df, pedigree_filename)
        return pedigree_filename, summary_filename, allele_filename

    return builder


@pytest.fixture
def variants_implementations(
        variants_vcf, variants_df, variants_thrift, variants_parquet):
    impls = {
        "variants_df": variants_df,
        "variants_vcf": variants_vcf,
        "variants_thrift": variants_thrift,
        "variants_parquet": variants_parquet,
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
