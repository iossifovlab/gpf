'''
Created on Feb 10, 2017

@author: lubo
'''
import pytest


def test_variant_types_empty(variant_types):
    data = {
        'variantTypes': []
    }
    assert variant_types.get_variant_types(**data) is None


def test_variant_types_missing(variant_types):
    data = {
    }
    assert variant_types.get_variant_types(**data) is None


def test_variant_types_all(variant_types):
    data = {
        'variantTypes': ["CNV", "del", "ins", "sub", "complex"]
    }
    assert variant_types.get_variant_types(**data) is None


def test_variant_types_single(variant_types):
    data = {
        'variantTypes': ["sub", ]
    }
    assert variant_types.get_variant_types(**data) == ['sub']


def test_variant_types_bad_with_safe(variant_types):
    data = {
        'variantTypes': ["sub", "bad"]
    }
    with pytest.raises(AssertionError):
        variant_types.get_variant_types(safe=True, **data)


def test_variant_types_bad_with_default_safe(variant_types):
    data = {
        'variantTypes': ["sub", "bad"]
    }
    with pytest.raises(AssertionError):
        variant_types.get_variant_types(**data)


def test_variant_types_bad_not_safe(variant_types):
    data = {
        'variantTypes': ["sub", "bad"]
    }
    assert variant_types.get_variant_types(safe=False, **data) == ['sub']
