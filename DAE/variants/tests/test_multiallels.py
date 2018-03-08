'''
Created on Feb 23, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
import numpy as np
from variants.variant import SummaryVariant, FamilyVariant


def test_multiallele_family_variant(fam1):
    sv = SummaryVariant(
        "1", 11539, "T", "TA,TG",
        atts={
            'effectType': np.array(['intron', 'intron']),
            'all.altFreq': np.array([50.49, 0.12]),
        })
    gt = np.array([[0, 0, 0],
                   [0, 0, 0]])

    fv = FamilyVariant.from_summary_variant(sv, fam1, gt=gt)
    assert fv is not None
    print(fv, fv['effectType'], fv['all.altFreq'])

    gt = np.array([[-1, 0, 0],
                   [0, 1, 0]])
    fv = FamilyVariant.from_summary_variant(sv, fam1, gt=gt)
    assert fv is not None

    print(fv, fv['effectType'], fv['all.altFreq'])

    gt = np.array([[-1, 0, 0],
                   [0, 1, 2]])
    fv = FamilyVariant.from_summary_variant(sv, fam1, gt=gt)
    assert fv is None

    gt = np.array([[-1, 0, 0],
                   [0, 2, 2]])
    fv = FamilyVariant.from_summary_variant(sv, fam1, gt=gt)
    assert fv is not None
    print(fv, fv['effectType'], fv['all.altFreq'])


def test_query_regions(ustudy):
    regions = [Region("1", 900717, 900717)]
    vs = ustudy.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 0
