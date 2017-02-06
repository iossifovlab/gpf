'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest


def test_none_dataset_id(query):
    with pytest.raises(AssertionError):
        query.get_variants(dataset_id=None)


def test_bad_dataset_id(query):
    with pytest.raises(AssertionError):
        query.get_variants(dataset_id='blah')


def test_good_dataset_id(query):
    query.get_variants(dataset_id='SSC')
