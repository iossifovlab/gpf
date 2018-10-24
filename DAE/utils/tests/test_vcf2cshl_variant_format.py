'''
Created on Mar 12, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

from utils.vcf_utils import vcf2cshl
from utils.dae_utils import dae2vcf_variant


def test_vcf2cshl_variant_format():
    #     res = vcf2cshl(1, 'A', ['AA', 'AC', 'G', 'GA', 'AC', 'ACAAC'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'A', 'AA')
    print(ps, vs)

    assert ps == 2
    assert vs == 'ins(A)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'AC')
    assert ps == 2
    assert vs == 'ins(C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'G')
    assert ps == 1
    assert vs == 'sub(A->G)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'GA')
    assert ps == 1
    assert vs == 'ins(G)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'AC')
    assert ps == 2
    assert vs == 'ins(C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'ACAAC')
    assert ps == 2
    assert vs == 'ins(CAAC)'
    assert ls == 4


def test_vcf2cshl_variant_format2():
    #     res = vcf2cshl(
    #         1, 'AA', ['AA', 'AC', 'AAA', 'A', 'AC', 'CA', 'ACAAC', 'CAAAAA'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'AA', 'AA')
    assert ps == 3
    assert vs == 'complex(->)'
    assert ls == 0

    ps, vs, ls = vcf2cshl(1, 'AA', 'AC')
    assert ps == 2
    assert vs == "sub(A->C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'AAA')
    assert ps == 3
    assert vs == "ins(A)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'AC')
    assert ps == 2
    assert vs == "sub(A->C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'CA')
    assert ps == 1
    assert vs == "sub(A->C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'ACAAC')
    assert ps == 2
    assert vs == "complex(A->CAAC)"
    assert ls == 4

    ps, vs, ls = vcf2cshl(1, 'AA', 'CAAAAA')
    assert ps == 1
    assert vs == "ins(CAAA)"
    assert ls == 4


def test_vcf2cshl_variant_format3():
    #     res = vcf2cshl(
    #         1, 'AAAAAA',
    #         ['AAAAAC', 'AAA', 'A', 'ACAAAA', 'CAAAAAA', 'AACAAC', 'CAAAAA'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AAAAAC')
    assert ps == 6
    assert vs == "sub(A->C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AAA')
    assert ps == 4
    assert vs == "del(3)"
    assert ls == 3

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'A')
    assert ps == 2
    assert vs == "del(5)"
    assert ls == 5

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'ACAAAA')
    assert ps == 2
    assert vs == "sub(A->C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'CAAAAAA')
    assert ps == 1
    assert vs == "ins(C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AACAAC')
    assert ps == 3
    assert vs == "complex(AAAA->CAAC)"
    assert ls == 4

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'CAAAAA')
    assert ps == 1
    assert vs == "sub(A->C)"
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AAAAAAC')
    assert ps == 7
    assert vs == "ins(C)"
    assert ls == 1


def test_insert_long():
    ref = 'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
    alt = 'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT' \
        'CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
    ps, vs, ls = vcf2cshl(1, ref, alt)
    print(ps, vs, ls)

    assert ps == 51  # FIXME


def test_cshl_to_vcf_problem():
    chrom = "2"
    position = 242815433
    variant = "sub(G->A)"

    chrom, position1, reference, alternative = \
        dae2vcf_variant(chrom, position, variant)
    print(chrom, position, reference, alternative)
    assert chrom == "2"
    assert position == position1
    assert reference == "G"
    assert alternative == "A"

    position2, variant2, length = vcf2cshl(position, reference, alternative)

    assert position2 == position
    assert variant2 == variant
    assert length == 1
