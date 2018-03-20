'''
Created on Mar 12, 2018

@author: lubo
'''
from __future__ import print_function

from variants.vcf_utils import vcf2cshl


def test_vcf2cshl_variant_format():
    #     res = vcf2cshl(1, 'A', ['AA', 'AC', 'G', 'GA', 'AC', 'ACAAC'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'A', ['AA'])
    print(ps, vs)

    assert ps[0] == 2
    assert vs[0] == 'ins(A)'
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'A', ['AC'])
    assert ps[0] == 2
    assert vs[0] == 'ins(C)'
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'A', ['G'])
    assert ps[0] == 1
    assert vs[0] == 'sub(A->G)'
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'A', ['GA'])
    assert ps[0] == 1
    assert vs[0] == 'ins(G)'
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'A', ['AC'])
    assert ps[0] == 2
    assert vs[0] == 'ins(C)'
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'A', ['ACAAC'])
    assert ps[0] == 2
    assert vs[0] == 'ins(CAAC)'
    assert ls[0] == 4


def test_vcf2cshl_variant_format2():
    #     res = vcf2cshl(
    #         1, 'AA', ['AA', 'AC', 'AAA', 'A', 'AC', 'CA', 'ACAAC', 'CAAAAA'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'AA', ['AA'])
    assert ps[0] == 3
    assert vs[0] == 'complex(->)'
    assert ls[0] == 0

    ps, vs, ls = vcf2cshl(1, 'AA', ['AC'])
    assert ps[0] == 2
    assert vs[0] == "sub(A->C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AA', ['AAA'])
    assert ps[0] == 3
    assert vs[0] == "ins(A)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AA', ['AC'])
    assert ps[0] == 2
    assert vs[0] == "sub(A->C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AA', ['CA'])
    assert ps[0] == 1
    assert vs[0] == "sub(A->C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AA', ['ACAAC'])
    assert ps[0] == 2
    assert vs[0] == "complex(A->CAAC)"
    assert ls[0] == 4

    ps, vs, ls = vcf2cshl(1, 'AA', ['CAAAAA'])
    assert ps[0] == 1
    assert vs[0] == "ins(CAAA)"
    assert ls[0] == 4


def test_vcf2cshl_variant_format3():
    #     res = vcf2cshl(
    #         1, 'AAAAAA',
    #         ['AAAAAC', 'AAA', 'A', 'ACAAAA', 'CAAAAAA', 'AACAAC', 'CAAAAA'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['AAAAAC'])
    assert ps[0] == 6
    assert vs[0] == "sub(A->C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['AAA'])
    assert ps[0] == 4
    assert vs[0] == "del(3)"
    assert ls[0] == 3

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['A'])
    assert ps[0] == 2
    assert vs[0] == "del(5)"
    assert ls[0] == 5

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['ACAAAA'])
    assert ps[0] == 2
    assert vs[0] == "sub(A->C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['CAAAAAA'])
    assert ps[0] == 1
    assert vs[0] == "ins(C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['AACAAC'])
    assert ps[0] == 3
    assert vs[0] == "complex(AAAA->CAAC)"
    assert ls[0] == 4

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['CAAAAA'])
    assert ps[0] == 1
    assert vs[0] == "sub(A->C)"
    assert ls[0] == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', ['AAAAAAC'])
    assert ps[0] == 7
    assert vs[0] == "ins(C)"
    assert ls[0] == 1


def test_insert_long():
    print("")
    ref = 'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
    alt = 'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT' \
        'CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
    ps, vs, ls = vcf2cshl(1, ref, [alt])
    print(ps, vs, ls)

    assert ps[0] == 51  # FIXME
