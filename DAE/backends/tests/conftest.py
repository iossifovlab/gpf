'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

# make sure env variables are set correctly
import findspark; findspark.init()  # noqa this needs to be the first import

from io import StringIO

import pytest
import os
import shutil
import tempfile

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
from backends.thrift.parquet_io import save_ped_df_to_parquet, \
    VariantsParquetWriter
from backends.thrift.raw_thrift import ThriftFamilyVariants

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

    family = Family.from_df("f1", ped_df)
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


@pytest.fixture(scope='session')
def variants_vcf(default_genome, default_gene_models):
    def builder(path):
        from backends.vcf.builder import variants_builder

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

    # def fin():
    #     shutil.rmtree(dirname)
    # request.addfinalizer(fin)

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
            member_filename=conf.member_variant)

        return conf

    return builder


# Impala backend

@pytest.fixture(scope='session')
def test_hdfs(request):
    from backends.impala.parquet_io import HdfsHelpers
    # hdfs = HdfsHelpers(host="dory.local", port=8020)
    hdfs = HdfsHelpers(host="172.18.0.1", port=8020)
    # hdfs = HdfsHelpers()
    return hdfs


@pytest.fixture(scope='session')
def impala_parquet_variants(request, test_hdfs, variants_vcf):
    dirname = test_hdfs.tempdir(prefix='variants_', suffix='_data')
    tempname = os.path.basename(dirname)

    # def fin():
    #     test_hdfs.delete(dirname)
    # request.addfinalizer(fin)

    def builder(path):
        from backends.impala.parquet_io import VariantsParquetWriter, \
            save_ped_df_to_parquet

        fvars = variants_vcf(path)
        assert not fvars.is_empty()

        basename = os.path.basename(path)
        fulldirname = os.path.join(dirname, basename)
        test_hdfs.mkdir(dirname)
        test_hdfs.mkdir(fulldirname)
        assert test_hdfs.exists(fulldirname)

        conf = Configure.from_prefix_impala(fulldirname, db=tempname).impala
        print(conf)

        save_ped_df_to_parquet(
            fvars.ped_df, conf.files.pedigree,
            filesystem=test_hdfs.filesystem())

        variants_builder = VariantsParquetWriter(
            fvars.full_variants_iterator())
        variants_builder.save_variants_to_parquet(
            conf.files.variants,
            filesystem=test_hdfs.filesystem())

        return conf

    return builder
