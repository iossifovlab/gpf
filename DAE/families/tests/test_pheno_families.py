'''
Created on Nov 10, 2016

@author: lubo
'''
from families.pheno_families import PhenoMeasureFilters, RaceFilter,\
    StudyFilters
import pytest


@pytest.fixture(scope='module')
def pheno_filters(request, measures):
    filters = PhenoMeasureFilters(measures)
    return filters


def test_get_matching_probands(pheno_filters):
    probands = pheno_filters.get_matching_probands(
        "pheno_common.non_verbal_iq", 9, 10)

    assert 1 == len(probands)


def test_get_matching_siblings(pheno_filters):
    siblings = pheno_filters.get_matching_siblings(
        "pheno_common.non_verbal_iq")
    assert 0 == len(siblings)


def test_filter_matching_probands(pheno_filters):
    prbs_all = pheno_filters.get_matching_probands(
        "pheno_common.non_verbal_iq")
    assert 2757 == len(prbs_all)

    prbs = pheno_filters.filter_matching_probands(
        prbs_all, "pheno_common.non_verbal_iq", 9, 10)
    assert 1 == len(prbs)


@pytest.fixture(scope='module')
def study_filters(request):
    sf = StudyFilters()
    return sf


def test_get_matching_probands_by_study_type(study_filters):
    probands = study_filters.get_matching_probands_by_study_type(
        "CNV")
    assert 2850 == len(probands)


def test_get_matching_probands_by_bad_study_name(study_filters):
    with pytest.raises(AssertionError):
        study_filters.get_matching_probands_by_study("ala bala")


def test_get_matching_probands_by_study_name(study_filters):
    probands = study_filters.get_matching_probands_by_study(
        "LevyCNV2011")
    assert 858 == len(probands)


def test_filter_matching_probadnds_by_study_name(study_filters):
    prbs1 = study_filters.get_matching_probands_by_study(
        "LevyCNV2011")
    prbs2 = study_filters.get_matching_probands_by_study(
        "IossifovWE2014")

    assert 858 == len(prbs1)
    assert 2508 == len(prbs2)

    prbs = study_filters.filter_matching_probands_by_study(
        prbs2, "LevyCNV2011")
    assert 771 == len(prbs)


def test_filter_matching_probands_by_study_type(study_filters):
    prbs1 = study_filters.get_matching_probands_by_study(
        "LevyCNV2011")
    prbs = study_filters.filter_matching_probands_by_study_type(
        prbs1, "TG")
    assert 768 == len(prbs)


@pytest.fixture(scope='module')
def race_filters(request, phdb):
    rf = RaceFilter(phdb)
    return rf


def test_other_race(race_filters, study_filters):
    res = race_filters.get_matching_probands_by_race('other')
    assert res is not None
    assert 72 == len(res)

    probands = study_filters.get_matching_probands_by_study(
        "LevyCNV2011")
    res = race_filters.filter_matching_probands_by_race(
        'other', probands)
    assert 14 == len(res)
