'''
Created on Feb 7, 2018

@author: lubo
'''
from variants.configure import Configure


def test_default_configure():
    conf = Configure.from_config()
    assert conf is not None
