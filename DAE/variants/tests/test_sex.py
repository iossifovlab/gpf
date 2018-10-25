'''
Created on Feb 23, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

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
