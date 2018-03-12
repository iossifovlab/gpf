'''
Created on Mar 12, 2018

@author: lubo
'''
from __future__ import print_function

from variants.vcf_utils import vcf2cshl


def test_vcf2cshl_variant_format():
    res = vcf2cshl(1, 'A', ['AA', 'AC', 'G', 'GA', 'AC', 'ACAAC'])
    print(res)

    res = vcf2cshl(1, 'A', ['AA'])
    print(res)

    p, v = res[0]
    assert p == 1
    assert v == 'ins(A)'

    res = vcf2cshl(1, 'A', ['AC'])
    print(res)

    p, v = res[0]
    assert p == 2
    assert v == 'ins(C)'

    res = vcf2cshl(1, 'A', ['G'])
    print(res)

    p, v = res[0]
    assert p == 1
    assert v == 'sub(A->G)'

    res = vcf2cshl(1, 'A', ['GA'])
    print(res)

    p, v = res[0]
    assert p == 1
    assert v == 'ins(G)'

    res = vcf2cshl(1, 'A', ['AC'])
    print(res)

    p, v = res[0]
    assert p == 2
    assert v == 'ins(C)'

    res = vcf2cshl(1, 'A', ['ACAAC'])
    print(res)

    p, v = res[0]
    assert p == 2
    assert v == 'ins(CAAC)'


def test_vcf2cshl_variant_format2():
    res = vcf2cshl(
        1, 'AA', ['AA', 'AC', 'AAA', 'A', 'AC', 'CA', 'ACAAC', 'CAAAAA'])
    print(res)

    res = vcf2cshl(1, 'AA', ['AA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v is None

    res = vcf2cshl(1, 'AA', ['AC'])
    print(res)
    p, v = res[0]
    assert p == 2
    assert v == "sub(A->C)"

    res = vcf2cshl(1, 'AA', ['AAA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "ins(A)"

    res = vcf2cshl(1, 'AA', ['AC'])
    print(res)
    p, v = res[0]
    assert p == 2
    assert v == "sub(A->C)"

    res = vcf2cshl(1, 'AA', ['CA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "sub(A->C)"

    res = vcf2cshl(1, 'AA', ['ACAAC'])
    print(res)
    p, v = res[0]
    assert p == 2
    assert v == "complex(A->CAAC)"

    res = vcf2cshl(1, 'AA', ['CAAAAA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "ins(CAAA)"


def test_vcf2cshl_variant_format3():
    res = vcf2cshl(
        1, 'AAAAAA',
        ['AAAAAC', 'AAA', 'A', 'ACAAAA', 'CAAAAAA', 'AACAAC', 'CAAAAA'])
    print(res)

    res = vcf2cshl(1, 'AAAAAA', ['AAAAAC'])
    print(res)
    p, v = res[0]
    assert p == 6
    assert v == "sub(A->C)"

    res = vcf2cshl(1, 'AAAAAA', ['AAA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "del(3)"

    res = vcf2cshl(1, 'AAAAAA', ['A'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "del(5)"

    res = vcf2cshl(1, 'AAAAAA', ['ACAAAA'])
    print(res)
    p, v = res[0]
    assert p == 2
    assert v == "sub(A->C)"

    res = vcf2cshl(1, 'AAAAAA', ['CAAAAAA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "ins(C)"

    res = vcf2cshl(1, 'AAAAAA', ['AACAAC'])
    print(res)
    p, v = res[0]
    assert p == 3
    assert v == "complex(AAAA->CAAC)"

    res = vcf2cshl(1, 'AAAAAA', ['CAAAAA'])
    print(res)
    p, v = res[0]
    assert p == 1
    assert v == "sub(A->C)"
