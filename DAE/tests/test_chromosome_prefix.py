'''
Created on May 7, 2018

@author: lubo
'''
from __future__ import unicode_literals
from Variant import chromosome_prefix


def test_chromosome_prefix():
    prefix = chromosome_prefix()
    assert prefix == "chr" or prefix == ""
    from DAE import genomesDB

    if "38" in genomesDB.defaultGenome:  # @UndefinedVariable
        assert prefix == 'chr'
    else:
        assert prefix == ''
