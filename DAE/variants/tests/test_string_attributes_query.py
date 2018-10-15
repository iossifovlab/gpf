'''
Created on Feb 27, 2018

@author: lubo
'''
from __future__ import unicode_literals
from variants.attributes import SexQuery, Sex, AQuery


def test_seq_query_simple():
    q = SexQuery.parse('male or female')

    assert q is not None
    assert q.match([Sex.male])


def test_string_query_or_simple():
    q = AQuery.parse('a or b')
    assert q.match(['a'])
    assert q.match(['b'])
    assert q.match(['a', 'b'])
    assert q.match(['a', 'b', 'c'])


def test_string_query_eq_simple():
    q = AQuery.parse('eq(a,b)')
    assert not q.match(['a'])
    assert not q.match(['b'])
    assert q.match(['a', 'b'])
    assert not q.match(['a', 'b', 'c'])


def test_string_query_any_simple():
    q = AQuery.parse('any(a, b)')
    assert q.match(['a'])
    assert q.match(['b'])
    assert q.match(['a', 'b'])
    assert q.match(['a', 'b', 'c'])


def test_string_query_all_simple():
    q = AQuery.parse('all(a, b)')
    assert not q.match(['a'])
    assert not q.match(['b'])
    assert q.match(['a', 'b'])
    assert q.match(['a', 'b', 'c'])


def test_string_query_and_simple():
    q = AQuery.parse('a and b')
    assert not q.match(['a'])
    assert not q.match(['b'])
    assert q.match(['a', 'b'])
    assert q.match(['a', 'b', 'c'])


def test_string_query_and_not_simple():
    q = AQuery.parse('a and not b')
    assert q.match(['a'])
    assert not q.match(['b'])
    assert not q.match(['a', 'b'])
    assert not q.match(['a', 'b', 'c'])
    assert q.match(['a', 'c'])
