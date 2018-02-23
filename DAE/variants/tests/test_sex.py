'''
Created on Feb 23, 2018

@author: lubo
'''
from variants.attributes import Sex


def test_sex_simple():
    s1 = Sex.from_value(1)

    assert s1 == Sex.male
