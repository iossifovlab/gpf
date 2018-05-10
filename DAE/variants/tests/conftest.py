'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function

import StringIO

import pytest

from variants.configure import Configure
from variants.family import Family
from variants.loader import RawVariantsLoader
from variants.raw_vcf import RawFamilyVariants
import os
import tempfile
import shutil
import numpy as np

from variants.annotate_variant_effects import \
    VcfVariantEffectsAnnotator
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.variant import VariantFactory, SummaryVariant,\
    VariantFactorySingle, FamilyVariant
from variants.attributes_query import parser as attributes_query_parser, \
    QueryTransformer

from variants.attributes_query import \
    parser_with_ambiguity as attributes_query_parser_with_ambiguity


@pytest.fixture(scope='session')
def effect_annotator():
    return VcfVariantEffectsAnnotator()


@pytest.fixture(scope='session')
def allele_freq_annotator():
    return VcfAlleleFrequencyAnnotator()


@pytest.fixture(scope='session')
def composite_annotator(effect_annotator, allele_freq_annotator):

    return AnnotatorComposite(annotators=[
        effect_annotator,
        allele_freq_annotator,
    ])


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
    return RawVariantsLoader(ustudy_config)


@pytest.fixture(scope='session')
def ustudy_single(ustudy_config, composite_annotator):
    fvariants = RawFamilyVariants(
        ustudy_config, annotator=composite_annotator,
        variant_factory=VariantFactorySingle)
    return fvariants


@pytest.fixture(scope='session')
def nvcf_config():
    from variants.default_settings import DATA_DIR
    prefix = os.path.join(DATA_DIR, "ssc_nygc/nssc")
    config = Configure.from_prefix(prefix)
    return config


@pytest.fixture(scope='session')
def nvcf(nvcf_config, composite_annotator):
    fvariants = RawFamilyVariants(nvcf_config, annotator=composite_annotator)
    return fvariants


@pytest.fixture(scope='session')
def uvcf_config():
    from variants.default_settings import DATA_DIR
    prefix = os.path.join(DATA_DIR, "ssc_nygc/ussc")
    config = Configure.from_prefix(prefix)
    return config


@pytest.fixture(scope='session')
def uvcf(uvcf_config, composite_annotator):
    fvariants = RawFamilyVariants(uvcf_config, annotator=composite_annotator)
    return fvariants


@pytest.fixture(scope='session')
def fvcf_config():
    from variants.default_settings import DATA_DIR
    prefix = os.path.join(DATA_DIR, "ssc_nygc/ssc")
    config = Configure.from_prefix(prefix)
    return config


@pytest.fixture(scope='session')
def fvcf(fvcf_config, composite_annotator):
    fvariants = RawFamilyVariants(fvcf_config, annotator=composite_annotator)
    return fvariants


@pytest.fixture(scope='session')
def nvcf19_config():
    from variants.default_settings import DATA_DIR
    prefix = os.path.join(DATA_DIR, "spark/nspark")
    config = Configure.from_prefix(prefix)
    return config


@pytest.fixture(scope='session')
def nvcf19s(nvcf19_config, composite_annotator):
    fvariants = RawFamilyVariants(
        nvcf19_config, annotator=composite_annotator,
        variant_factory=VariantFactorySingle)
    return fvariants


@pytest.fixture(scope='session')
def nvcf19f(nvcf19_config, composite_annotator):
    fvariants = RawFamilyVariants(
        nvcf19_config, annotator=composite_annotator,
        variant_factory=VariantFactory)
    return fvariants


@pytest.fixture(scope='session')
def vcf19_config():
    from variants.default_settings import DATA_DIR
    prefix = os.path.join(DATA_DIR, "spark/spark")
    config = Configure.from_prefix(prefix)
    return config


@pytest.fixture(scope='session')
def vcf19r(vcf19_config, composite_annotator):

    def builder(region):
        return RawFamilyVariants(
            vcf19_config, region=region, annotator=composite_annotator)

    return builder


@pytest.fixture(scope='session')
def single_vcf(composite_annotator):
    def builder(path):
        a_data = relative_to_this_test_folder(path)
        a_conf = Configure.from_prefix(a_data)
        fvars = RawFamilyVariants(
            a_conf, annotator=composite_annotator,
            variant_factory=VariantFactorySingle)
        return fvars
    return builder


@pytest.fixture(scope='session')
def full_vcf(composite_annotator):
    def builder(path):
        a_data = relative_to_this_test_folder(path)
        a_conf = Configure.from_prefix(a_data)
        fvars = RawFamilyVariants(
            a_conf, annotator=composite_annotator,
            variant_factory=VariantFactory)
        return fvars
    return builder


@pytest.fixture(scope='session')
def data_vcf19(composite_annotator):
    def builder(path):
        from variants.default_settings import DATA_DIR
        a_prefix = os.path.join(DATA_DIR, path)
        a_conf = Configure.from_prefix(a_prefix)
        fvars = RawFamilyVariants(
            a_conf, annotator=composite_annotator,
            variant_factory=VariantFactory)
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
    return SummaryVariant("1", 11539, "T", ["TA", "TG"])


@pytest.fixture(scope='session')
def fv1(fam1, sv):
    def rfun(gt):
        return FamilyVariant(sv, fam1, gt)
    return rfun


@pytest.fixture(scope='session')
def fv_one(fam1, sv):
    return VariantFactory.family_variant_from_gt(
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
def transformer():
    return QueryTransformer
