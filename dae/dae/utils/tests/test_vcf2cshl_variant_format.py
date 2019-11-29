'''
Created on Mar 12, 2018

@author: lubo
'''
from dae.utils.variant_utils import vcf2cshl, trim_str_back
from dae.utils.dae_utils import dae2vcf_variant


def test_vcf2cshl_variant_format():
    #     res = vcf2cshl(1, 'A', ['AA', 'AC', 'G', 'GA', 'AC', 'ACAAC'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'A', 'AA', trimmer=trim_str_back)
    print(ps, vs)

    assert ps == 1
    assert vs == 'ins(A)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'AC', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'ins(C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'G', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'sub(A->G)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'GA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'ins(G)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'AC', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'ins(C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'A', 'ACAAC', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'ins(CAAC)'
    assert ls == 4


def test_vcf2cshl_variant_format2():
    #     res = vcf2cshl(
    #         1, 'AA', ['AA', 'AC', 'AAA', 'A', 'AC', 'CA', 'ACAAC', 'CAAAAA'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'AA', 'AA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'complex(->)'
    assert ls == 0

    ps, vs, ls = vcf2cshl(1, 'AA', 'AC', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'sub(A->C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'AAA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'ins(A)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'AC', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'sub(A->C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'CA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'sub(A->C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AA', 'ACAAC', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'complex(A->CAAC)'
    assert ls == 4

    ps, vs, ls = vcf2cshl(1, 'AA', 'CAAAAA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'ins(CAAA)'
    assert ls == 4


def test_vcf2cshl_variant_format3():
    #     res = vcf2cshl(
    #         1, 'AAAAAA',
    #         ['AAAAAC', 'AAA', 'A', 'ACAAAA', 'CAAAAAA', 'AACAAC', 'CAAAAA'])
    #     print(res)

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AAAAAC', trimmer=trim_str_back)
    assert ps == 6
    assert vs == 'sub(A->C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AAA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'del(3)'
    assert ls == 3

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'A', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'del(5)'
    assert ls == 5

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'ACAAAA', trimmer=trim_str_back)
    assert ps == 2
    assert vs == 'sub(A->C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'CAAAAAA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'ins(C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AACAAC', trimmer=trim_str_back)
    assert ps == 3
    assert vs == 'complex(AAAA->CAAC)'
    assert ls == 4

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'CAAAAA', trimmer=trim_str_back)
    assert ps == 1
    assert vs == 'sub(A->C)'
    assert ls == 1

    ps, vs, ls = vcf2cshl(1, 'AAAAAA', 'AAAAAAC', trimmer=trim_str_back)
    assert ps == 7
    assert vs == 'ins(C)'
    assert ls == 1


def test_insert_long():
    ref = 'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
    alt = 'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT' \
        'CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
    ps, vs, ls = vcf2cshl(1, ref, alt, trimmer=trim_str_back)
    print(ps, vs, ls)

    assert ps == 2  # FIXME


def test_cshl_to_vcf_problem(default_genome):
    chrom = '2'
    position = 242815433
    variant = 'sub(G->A)'

    position1, reference, alternative = \
        dae2vcf_variant(chrom, position, variant, default_genome)
    print(chrom, position, reference, alternative)
    assert chrom == '2'
    assert position == position1
    assert reference == 'G'
    assert alternative == 'A'

    position2, variant2, length = vcf2cshl(
        position, reference, alternative, trimmer=trim_str_back)

    assert position2 == position
    assert variant2 == variant
    assert length == 1


def test_spark_v3_problems_check():

    # chrom = '1'
    position = 865461
    ref = 'AGCCCCACCTTCCTCTCCTCCT'
    alt = 'AGCCCCACCTTCCTCTCCTCCT' \
        'GCCCCACCTTCCTCTCCTCCT'

    pos1, var1, len1 = vcf2cshl(position, ref, alt, trimmer=trim_str_back)

    assert var1 == 'ins(GCCCCACCTTCCTCTCCTCCT)'
    assert pos1 == position + 1
