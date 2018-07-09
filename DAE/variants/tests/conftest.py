'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function

import StringIO
import os
import shutil
import tempfile
import time

import pytest

import numpy as np
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
from variants.family import Family
from variants.family_variant import FamilyVariant
from variants.loader import RawVariantsLoader
from variants.parquet_io import family_variants_df, save_summary_to_parquet,\
    save_family_variants_df_to_parquet, save_ped_df_to_parquet,\
    save_f2s_df_to_parquet
from variants.raw_df import DfFamilyVariants
from variants.raw_thrift import ThriftFamilyVariants
from variants.raw_vcf import RawFamilyVariants, \
    VariantFactoryMulti
from variants.variant import SummaryAllele, SummaryVariant


@pytest.fixture(scope='session')
def effect_annotator():
    return VcfVariantEffectsAnnotator()


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
def testing_thriftserver_port():
    thrift_port = os.environ.get("THRIFTSERVER_PORT")
    if thrift_port is None:
        return 10000
    return int(thrift_port)


@pytest.fixture(scope='session')
def testing_thriftserver(request):
    from impala.dbapi import connect

    spark_home = os.environ.get("SPARK_HOME")
    assert spark_home is not None

    thrift_port = os.environ.get("THRIFTSERVER_PORT")
    if thrift_port is not None:
        thrift_port = int(thrift_port)
    else:
        thrift_port = 10000

    def thrift_connect():
        for count in range(10):
            try:
                time.sleep(2.0)
                print("trying to connect to thrift server: try={}".format(
                    count))
                conn = connect(host='127.0.0.1', port=thrift_port,
                               auth_mechanism='PLAIN')
                return conn
            except Exception as ex:
                print("connect to thriftserver failed:", ex)
        return None

    conn = thrift_connect()
    if conn is not None:
        return conn

    start_cmd = "{}/sbin/start-thriftserver.sh " \
        "--hiveconf hive.server2.thrift.port={}".format(
            spark_home, thrift_port)
    stop_cmd = "{}/sbin/stop-thriftserver.sh".format(spark_home)

    def fin():
        print("stoping  thrift command: ", stop_cmd)
        os.system(stop_cmd)
    request.addfinalizer(fin)

    print("starting thrift command: ", start_cmd)
    status = os.system(start_cmd)
    assert status == 0

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
def ustudy_config():
    config = Configure.from_config()
    return config


@pytest.fixture(scope='session')
def ustudy_loader(ustudy_config):
    return RawVariantsLoader(ustudy_config.vcf)


@pytest.fixture(scope='session')
def ustudy_vcf(ustudy_config, composite_annotator):
    fvariants = RawFamilyVariants(
        ustudy_config, annotator=composite_annotator,
        variant_factory=VariantFactoryMulti)
    return fvariants


@pytest.fixture(scope='session')
def variants_vcf(composite_annotator):
    def builder(path):
        a_data = relative_to_this_test_folder(path)
        a_conf = Configure.from_prefix_vcf(a_data)
        fvars = RawFamilyVariants(
            a_conf, annotator=composite_annotator,
            variant_factory=VariantFactoryMulti)
        return fvars
    return builder


@pytest.fixture(scope='session')
def variants_df(variants_vcf):
    def builder(path):
        fvars = variants_vcf(path)
        summary_df = fvars.annot_df
        ped_df = fvars.ped_df
        vars_df, f2s_df = family_variants_df(
            fvars.query_variants(
            ))
        return DfFamilyVariants(ped_df, summary_df, vars_df, f2s_df)
    return builder


@pytest.fixture(scope='session')
def variants_thrift(parquet_variants, testing_thriftserver):
    def builder(path):
        pedigree, summary, family, f2s = parquet_variants(path)
        config = Configure.from_dict({
            'parquet': {
                'pedigree': pedigree,
                'summary': summary,
                'family': family,
                'f2s': f2s,
            }
        })
        return ThriftFamilyVariants(
            config=config,
            thrift_connection=testing_thriftserver)
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
        family_filename = os.path.join(
            fulldirname, "family.parquet")
        f2s_filename = os.path.join(
            fulldirname, "f2s.parquet")
        pedigree_filename = os.path.join(
            fulldirname, "pedigree.parquet")

        if os.path.exists(summary_filename) and \
                os.path.exists(family_filename) and \
                os.path.exists(f2s_filename) and \
                os.path.exists(pedigree_filename):
            return pedigree_filename, summary_filename, \
                family_filename, f2s_filename

        if not os.path.exists(fulldirname):
            os.mkdir(fulldirname)

        assert os.path.exists(fulldirname)
        assert os.path.isdir(fulldirname)

        fvars = variants_df(path)
        save_summary_to_parquet(fvars.summary_df, summary_filename)
        save_family_variants_df_to_parquet(fvars.vars_df, family_filename)
        save_f2s_df_to_parquet(fvars.f2s_df, f2s_filename)
        save_ped_df_to_parquet(fvars.ped_df, pedigree_filename)
        return pedigree_filename, summary_filename, \
            family_filename, f2s_filename

    return builder


@pytest.fixture
def variants_implementations(variants_vcf, variants_df, variants_thrift):
    impls = {
        "variants_df": variants_df,
        "variants_vcf": variants_vcf,
        "variants_thrift": variants_thrift,
    }
    return impls


@pytest.fixture
def variants_impl(variants_implementations):
    return lambda impl_name: variants_implementations[impl_name]


@pytest.fixture(scope='session')
def data_vcf19(composite_annotator):
    def builder(path):
        from variants.default_settings import DATA_DIR
        a_prefix = os.path.join(DATA_DIR, path)
        a_conf = Configure.from_prefix_vcf(a_prefix)
        fvars = RawFamilyVariants(
            a_conf, annotator=composite_annotator,
            variant_factory=VariantFactoryMulti)
        return fvars
    return builder


PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""


@pytest.fixture(scope='session')
def fam1():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED1), sep=",")

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


@pytest.fixture(scope='session')
def fv_one(fam1, sv):
    return VariantFactoryMulti.family_variant_from_gt(
        sv, fam1, np.array([[1, 1, 1], [0, 0, 0]]))[0]


PED2 = """
# SIMPLE QUAD
familyId,    personId,    dadId,    momId,    sex,    status,    role
f1,          d1,          0,        0,        1,      1,         dad
f1,          m1,          0,        0,        2,      1,         mom
f1,          p1,          d1,       m1,       1,      2,         prb
f1,          s1,          d1,       m1,       1,      1,         sib
"""


@pytest.fixture(scope='session')
def fam2():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED2), sep=',')

    family = Family("f1", ped_df)
    assert len(family.trios) == 2
    return family


@pytest.fixture(scope='session')
def fv2(sv, fam2):
    def rfun(gt):
        return FamilyVariant(sv, fam2, gt)
    return rfun


PED3 = """
# TWO GENERATION PEDIGREE
familyId, personId, dadId, momId, sex,   status, role
f1,       gd1,      0,     0,     1,     1,      pathernal_grandfather
f1,       gm1,      0,     0,     2,     1,      pathernal_grandmother
f1,       d1,       gd1,   gm1,   1,     1,      dad
f1,       m1,       0,     0,     2,     1,      mom
f1,       p1,       d1,    m1,    1,     2,      prb
"""


@pytest.fixture(scope='session')
def fam3():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED3), sep=',')

    family = Family("f1", ped_df)
    assert len(family.trios) == 2
    return family


@pytest.fixture(scope='session')
def fv3(sv, fam3):
    def rfun(gt):
        return FamilyVariant(sv, fam3, gt)
    return rfun


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


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
