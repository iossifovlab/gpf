"""
Created on Mar 12, 2018

@author: lubo
"""
from dae.variants.core import Allele
import pytest

from dae.variants.variant import vcf2cshl, trim_str_right_left, \
    tandem_repeat
from dae.utils.dae_utils import dae2vcf_variant


@pytest.mark.parametrize(
    "ref,alt,vt,pos,length", [

        ("A", "AA",
         "ins(A)",
         1, 1),

        ("A", "AC",
         "ins(C)",
         2, 1),

        ("A", "G",
         "sub(A->G)",
         1, 1),

        ("A", "GA",
         "ins(G)",
         1, 1),

        ("A", "AC",
         "ins(C)",
         2, 1),

        ("A", "ACAAC",
         "ins(CAAC)",
         2, 4),
    ])
def test_vcf2cshl_variant_format(ref, alt, vt, pos, length):

    vd = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)

    assert vd.position == pos
    assert str(vd) == vt
    assert vd.length == length


@pytest.mark.parametrize(
    "ref,alt,vt,pos,length", [

        ("AA", "AA",
         "comp(->)",
         1, 0),

        ("AA", "AAA",
         "ins(A)",
         1, 1),

        ("AA", "AC",
         "sub(A->C)",
         2, 1),

        ("AA", "CA",
         "sub(A->C)",
         1, 1),

        ("AA", "ACAAC",
         "comp(A->CAAC)",
         2, 4),

        ("AA", "CAAAAA",
         "ins(CAAA)",
         1, 4),
    ])
def test_vcf2cshl_variant_format2(ref, alt, vt, pos, length):

    vd = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)
    assert vd.position == pos
    assert str(vd) == vt
    assert vd.length == length


@pytest.mark.parametrize(
    "ref,alt,vt,pos,length", [

        ("AAAAAA", "AAAAAC",
         "sub(A->C)",
         6, 1),

        ("AAAAAA", "AAA",
         "del(3)",
         1, 3),

        ("AAAAAA", "A",
         "del(5)",
         1, 5),

        ("AAAAAA", "ACAAAA",
         "sub(A->C)",
         2, 1),

        ("AAAAAA", "CAAAAAA",
         "ins(C)",
         1, 1),

        ("AAAAAA", "AACAAC",
         "comp(AAAA->CAAC)",
         3, 4),

        ("AAAAAA", "CAAAAA",
         "sub(A->C)",
         1, 1),

        ("AAAAAA", "AAAAAAC",
         "ins(C)",
         7, 1),
    ])
def test_vcf2cshl_variant_format3(ref, alt, vt, pos, length):

    vd = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)
    assert vd.position == pos
    assert str(vd) == vt
    assert vd.length == length


def test_insert_long():
    ref = "CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
    alt = (
        "CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
        "CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
    )
    vd = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)

    assert vd.position == 2  # FIXME


def test_cshl_to_vcf_problem(genome_2013):
    chrom = "2"
    position = 242815433
    variant = "sub(G->A)"

    position1, reference, alternative = dae2vcf_variant(
        chrom, position, variant, genome_2013
    )
    print(chrom, position, reference, alternative)
    assert chrom == "2"
    assert position == position1
    assert reference == "G"
    assert alternative == "A"

    vd = vcf2cshl(
        position, reference, alternative, trimmer=trim_str_right_left
    )

    assert vd.position == position
    assert str(vd) == variant
    assert vd.length == 1


def test_spark_v3_problems_check():

    # chrom = '1'
    position = 865461
    ref = "AGCCCCACCTTCCTCTCCTCCT"
    alt = "AGCCCCACCTTCCTCTCCTCCT" "GCCCCACCTTCCTCTCCTCCT"

    vd = vcf2cshl(position, ref, alt, trimmer=trim_str_right_left)

    assert str(vd) == "ins(GCCCCACCTTCCTCTCCTCCT)"
    assert vd.position == position + 1


@pytest.mark.parametrize(
    "chrom,position,ref,alt,unit,ref_repeats,alt_repeats", [

        ("chr1", 13886145,
         "ATCCATCCATCCATCCATCCATCCATCCATCC",
         "ATCCATCCATCCATCCATCCATCCATCCATCCATCC",
         "ATCC", 8, 9),

        ("chr1", 28876285,
         "AAAAAAAAAAAAAAAAAAAAA",
         "AAAAAAAAAAAAAAAAA",
         "A", 21, 17),

        ("chr1", 33643893,
         "GGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAA",
         "GGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAA",
         "GGAA", 11, 12),

        ("chr1", 1005758,
         "GCCCCCGCAGCAGTGCCCCCGCAGCAGT",
         "GCCCCCGCAGCAGT",
         "GCCCCCGCAGCAGT", 2, 1),

        ("chr1", 1013550,
         "GCCCACAGCCCACAGCCCACA",
         "GCCCACAGCCCACA",
         "GCCCACA", 3, 2),

        ("chr1", 1053180,
         "TGTCTGCACGTGGGTGTCTGCACGTGGG",
         "TGTCTGCACGTGGG",
         "TGTCTGCACGTGGG", 2, 1),

        ("chr1", 1053180,
         "TGTCTGCACGTGGGTGTCTGCACGTGGG",
         "TGTCTGCACGTGGGTGTCTGCACGTGGGTGTCTGCACGTGGG",
         "TGTCTGCACGTGGG", 2, 3),

        ("chr1", 1053180,
         "CGCCCCTGCCCTGGAGGCCCCGCCCCTGCCCTGGAGGCCCCGCCCCTGCCCTGGAGGCCC",
         "CGCCCCTGCCCTGGAGGCCC",
         "CGCCCCTGCCCTGGAGGCCC", 3, 1),

    ])
def test_tandem_repeat_unit(
        chrom, position, ref, alt, unit, ref_repeats, alt_repeats):

    tr_unit, tr_ref, tr_alt = tandem_repeat(ref, alt)
    assert tr_unit is not None
    assert tr_ref is not None
    assert tr_alt is not None
    assert tr_unit == unit
    assert tr_ref == ref_repeats
    assert tr_alt == alt_repeats

    vd = vcf2cshl(position, ref, alt)
    assert vd.variant_type & Allele.Type.tandem_repeat
    if ref_repeats < alt_repeats:
        assert vd.variant_type & Allele.Type.small_insertion
    elif ref_repeats > alt_repeats:
        assert vd.variant_type & Allele.Type.small_deletion
