'''
Created on Feb 23, 2018

@author: lubo
'''
from __future__ import print_function

from variants.attributes import Sex, SexQuery
import pytest


def test_sex_attribute():

    assert Sex.from_value(1) == Sex.male
    assert Sex.from_name('M') == Sex.male
    assert Sex.from_name('male') == Sex.male

    assert Sex.from_value(2) == Sex.female
    assert Sex.from_name('F') == Sex.female
    assert Sex.from_name('female') == Sex.female

    assert Sex.from_value(4) == Sex.unspecified
    assert Sex.from_name('U') == Sex.unspecified
    assert Sex.from_name('unspecified') == Sex.unspecified


def test_bad_sex_value():
    with pytest.raises(ValueError):
        Sex.from_value(100)


def test_bad_sex_name():
    with pytest.raises(ValueError):
        Sex.from_name("gaga")


def test_seq_query_simple():
    q = SexQuery.parse('male or female')

    assert q is not None
    assert q.match([Sex.male])
    assert q.match([Sex.female])
    assert q.match([Sex.male, Sex.female])
    assert not q.match([Sex.unspecified])


def test_seq_query_complex():
    q = SexQuery.parse('male and not female')

    assert q is not None
    assert q.match([Sex.male])
    assert not q.match([Sex.female])
    assert not q.match([Sex.male, Sex.female])
    assert not q.match([Sex.unspecified])


def test_query_sexes_male_only(uagre):
    vs = uagre.query_variants(sexes='male and not female')
    vl = list(vs)

    assert len(vl) == 42
    for v in vl:
        assert set(v.variant_in_sexes) == set([Sex.male])


def test_query_sexes_male_only_eq(uagre):
    vs = uagre.query_variants(sexes='eq(male)')
    vl = list(vs)

    assert len(vl) == 42
    for v in vl:
        assert set(v.variant_in_sexes) == set([Sex.male])


def test_query_sexes_female_only(uagre):
    vs = uagre.query_variants(sexes='female and not male')
    vl = list(vs)

    assert len(vl) == 36
    for v in vl:
        assert set(v.variant_in_sexes) == set([Sex.female])


def test_query_sexes_female_only_eq(uagre):
    vs = uagre.query_variants(sexes='eq(female)')
    vl = list(vs)

    assert len(vl) == 36
    for v in vl:
        assert set(v.variant_in_sexes) == set([Sex.female])


def test_query_sexes_single_sex_only(uagre):
    vs = uagre.query_variants(
        sexes="(male and not female) or (female and not male)")
    assert vs is not None

    vl = list(vs)

    for v in vl:
        assert len(v.variant_in_sexes) == 1
    assert len(vl) == 78


def test_query_sexes_single_sex_only_eq(uagre):
    vs = uagre.query_variants(
        sexes="eq(male) or eq(female)")
    assert vs is not None

    vl = list(vs)

    for v in vl:
        assert len(v.variant_in_sexes) == 1
    assert len(vl) == 78
