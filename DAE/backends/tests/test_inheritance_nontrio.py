'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

from RegionOperations import Region
from variants.attributes import Inheritance


@pytest.mark.parametrize("region,count,inheritance", [
    (Region('1', 11500, 11500), 1, Inheritance.unknown),
    (Region('1', 11501, 11501), 1, Inheritance.unknown),
    (Region('1', 11502, 11502), 1, Inheritance.unknown),
    (Region('1', 11503, 11503), 1, Inheritance.unknown),
    (Region('1', 11504, 11504), 1, Inheritance.unknown),
    (Region('1', 11505, 11505), 1, Inheritance.unknown),
])
def test_inheritance_nontrio(variants_vcf, region, count, inheritance):
    fvars = variants_vcf("fixtures/inheritance_nontrio")
    vs = list(fvars.query_variants(
        regions=[region],
        family_ids=['f1'],
        return_reference=True,
        return_unknown=True))

    assert len(vs) == count
    for v in vs:
        for aa in v.alt_alleles:
            print(aa.inheritance_in_members)
            assert set(aa.inheritance_in_members) == set([Inheritance.unknown])
