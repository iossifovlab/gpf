'''
Created on Jul 21, 2017

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
import pprint
import pytest


# def test_datasets_description_simple(datasets_config):
#     pprint.pprint(datasets_config)
#
#     test = datasets_config.get_dataset_desc("TEST")
#     assert test is not None
#
#     print(test["description"])
#     assert test['description'] is not None

@pytest.mark.skip(reason="no way of currently testing this")
def test_datasets_missing_description_simple(datasets_config):
    pprint.pprint(datasets_config)

    test = datasets_config.get_dataset_desc("SPARK")
    assert test is not None

    print(test["description"])
    assert test['description'] is not None
