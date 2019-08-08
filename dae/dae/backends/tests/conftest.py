'''
Created on Feb 7, 2018

@author: lubo
'''
from io import StringIO

import pytest

from dae.variants.family import Family, FamiliesBase
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant


from ..vcf.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator


@pytest.fixture(scope='session')
def allele_freq_annotator():
    return VcfAlleleFrequencyAnnotator()


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
        return FamilyVariant.from_sumary_variant(sv, fam1, gt)
    return rfun
