# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.variants.core import Allele
from dae.variants.variant import tandem_repeat, trim_str_right_left, vcf2cshl


@pytest.mark.parametrize(
    "ref,alt,variant_type,pos,length", [

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

        ("A", "ACAAC",
         "ins(CAAC)",
         2, 4),
    ])
def test_vcf2cshl_variant_format(
        ref: str, alt: str, variant_type: str, pos: int, length: int) -> None:

    variant_desc = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)

    assert variant_desc.position == pos
    assert str(variant_desc) == variant_type
    assert variant_desc.length == length


@pytest.mark.parametrize(
    "ref,alt,variant_type,pos,length", [

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
def test_vcf2cshl_variant_format2(
        ref: str, alt: str, variant_type: str, pos: int, length: int) -> None:

    variant_desc = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)
    assert variant_desc.position == pos
    assert str(variant_desc) == variant_type
    assert variant_desc.length == length


@pytest.mark.parametrize(
    "ref,alt,variant_type,pos,length", [

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
def test_vcf2cshl_variant_format3(
        ref: str, alt: str, variant_type: str, pos: int, length: int) -> None:

    variant_desc = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)
    assert variant_desc.position == pos
    assert str(variant_desc) == variant_type
    assert variant_desc.length == length


def test_insert_long() -> None:
    ref = "CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
    alt = (
        "CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
        "CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
    )
    variant_desc = vcf2cshl(1, ref, alt, trimmer=trim_str_right_left)

    assert variant_desc.position == 2


def test_spark_v3_problems_check() -> None:

    position = 865461
    ref = "AGCCCCACCTTCCTCTCCTCCT"
    alt = "AGCCCCACCTTCCTCTCCTCCT" + "GCCCCACCTTCCTCTCCTCCT"

    variant_desc = vcf2cshl(position, ref, alt, trimmer=trim_str_right_left)

    assert str(variant_desc) == "ins(GCCCCACCTTCCTCTCCTCCT)"
    assert variant_desc.position == position + 1


@pytest.mark.parametrize(
    "position,ref,alt,unit,ref_repeats,alt_repeats", [

        (13886145,
         "ATCCATCCATCCATCCATCCATCCATCCATCC",
         "ATCCATCCATCCATCCATCCATCCATCCATCCATCC",
         "ATCC", 8, 9),

        (28876285,
         "AAAAAAAAAAAAAAAAAAAAA",
         "AAAAAAAAAAAAAAAAA",
         "A", 21, 17),

        (33643893,
         "GGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAA",
         "GGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAAGGAA",
         "GGAA", 11, 12),

        (1005758,
         "GCCCCCGCAGCAGTGCCCCCGCAGCAGT",
         "GCCCCCGCAGCAGT",
         "GCCCCCGCAGCAGT", 2, 1),

        (1013550,
         "GCCCACAGCCCACAGCCCACA",
         "GCCCACAGCCCACA",
         "GCCCACA", 3, 2),

        (1053180,
         "TGTCTGCACGTGGGTGTCTGCACGTGGG",
         "TGTCTGCACGTGGG",
         "TGTCTGCACGTGGG", 2, 1),

        (1053180,
         "TGTCTGCACGTGGGTGTCTGCACGTGGG",
         "TGTCTGCACGTGGGTGTCTGCACGTGGGTGTCTGCACGTGGG",
         "TGTCTGCACGTGGG", 2, 3),

        (1053180,
         "CGCCCCTGCCCTGGAGGCCCCGCCCCTGCCCTGGAGGCCCCGCCCCTGCCCTGGAGGCCC",
         "CGCCCCTGCCCTGGAGGCCC",
         "CGCCCCTGCCCTGGAGGCCC", 3, 1),

    ])
def test_tandem_repeat_unit(
        position: int,
        ref: str, alt: str,
        unit: str, ref_repeats: int, alt_repeats: int) -> None:

    tr_unit, tr_ref, tr_alt = tandem_repeat(ref, alt)
    assert tr_unit is not None
    assert tr_ref is not None
    assert tr_alt is not None
    assert tr_unit == unit
    assert tr_ref == ref_repeats
    assert tr_alt == alt_repeats

    variant_desc = vcf2cshl(position, ref, alt)
    assert variant_desc.variant_type & Allele.Type.tandem_repeat
    if ref_repeats < alt_repeats:
        assert variant_desc.variant_type & Allele.Type.small_insertion
    elif ref_repeats > alt_repeats:
        assert variant_desc.variant_type & Allele.Type.small_deletion
