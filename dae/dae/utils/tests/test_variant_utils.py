# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import List, Union

import pytest
import numpy as np

from dae.utils.variant_utils import get_locus_ploidy, reverse_complement, \
    gt2str, str2gt, trim_str_right, trim_str_left, \
    trim_parsimonious
from dae.variants.attributes import Sex


chroms: List[Union[int, str]] = list(range(1, 23))
chroms.append("Y")

test_data = [
    (str(chrom), 123123, sex, 2)
    for sex in (Sex.M, Sex.F)
    for chrom in list(range(1, 23))
]
test_data.append(("X", 1, Sex.F, 2))
test_data.append(("X", 60001, Sex.F, 2))
test_data.append(("X", 100000, Sex.F, 2))
test_data.append(("X", 2700000, Sex.F, 2))
test_data.append(("X", 154931044, Sex.F, 2))
test_data.append(("X", 154931050, Sex.F, 2))
test_data.append(("X", 155260560, Sex.F, 2))
test_data.append(("X", 155260600, Sex.F, 2))
test_data.append(("X", 1, Sex.M, 1))
test_data.append(("X", 60001, Sex.M, 2))
test_data.append(("X", 100000, Sex.M, 2))
test_data.append(("X", 2700000, Sex.M, 1))
test_data.append(("X", 154931044, Sex.M, 2))
test_data.append(("X", 154931050, Sex.M, 2))
test_data.append(("X", 155260560, Sex.M, 2))
test_data.append(("X", 155260600, Sex.M, 1))

# test_data_chr_prefix = list(
#     map(lambda x: ("chr" + x[0], x[1], x[2], x[3]), test_data)
# )
# test_data.extend(test_data_chr_prefix)


@pytest.mark.parametrize("chrom,pos,sex,expected", [*test_data])
def test_get_locus_ploidy(chrom, pos, sex, expected, gpf_instance_2013):
    genomic_sequence = gpf_instance_2013.reference_genome
    assert get_locus_ploidy(chrom, pos, sex, genomic_sequence) == expected


@pytest.mark.parametrize("dna,expected", [
    ("a", "T"),
    ("ac", "GT"),
    ("actg", "CAGT"),
])
def test_reverse_complement(dna, expected):
    result = reverse_complement(dna)
    assert result == expected


@pytest.mark.parametrize("gt,expected", [
    (
        np.array([[0, 0, 0], [0, 1, 0]], dtype=np.int8),
        "0/0,0/1,0/0"
    ),
    (
        np.array([[0, 0, 0], [0, -1, 0]], dtype=np.int8),
        "0/0,0/.,0/0"
    ),
    (
        np.array([[0, 1, 0], [0, -1, 0]], dtype=np.int8),
        "0/0,1/.,0/0"
    ),
])
def test_gt2str(gt, expected):
    res = gt2str(gt)

    assert res == expected


@pytest.mark.parametrize("gts,expected", [
    (
        "0/0,0/1,0/0",
        np.array([[0, 0, 0], [0, 1, 0]], dtype=np.int8),
    ),
    (
        "0/0,0/.,0/0",
        np.array([[0, 0, 0], [0, -1, 0]], dtype=np.int8),
    ),
    (
        "0/0,1/.,0/0",
        np.array([[0, 1, 0], [0, -1, 0]], dtype=np.int8),
    ),
])
def test_str2gt(gts, expected):
    res = str2gt(gts)

    assert np.all(res == expected)


@pytest.mark.parametrize("pos,ref,alt,trim_pos,trim_ref,trim_alt", [
    (1, "AA", "CA", 1, "A", "C"),
    (1, "AAA", "CCA", 1, "AA", "CC"),
    (1, "AAA", "ACA", 1, "AA", "AC"),
    (100, "TGGTGCAGGC", "T", 100, "TGGTGCAGGC", "T"),
    (100, "TGGTGCAGGC", "CGGTGCAGGC", 100, "T", "C"),
    (100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC", 100, "T", "TGGTGCAGGC"),
    (100, "TGGTGCAGGC", "TGGTGCAGGT", 100, "TGGTGCAGGC", "TGGTGCAGGT"),
])
def test_trim_str_right(pos, ref, alt, trim_pos, trim_ref, trim_alt):

    tpos, tref, talt = trim_str_right(pos, ref, alt)
    assert trim_pos == tpos
    assert trim_ref == tref
    assert trim_alt == talt


@pytest.mark.parametrize("pos,ref,alt,trim_pos,trim_ref,trim_alt", [
    (1, "AA", "CA", 1, "AA", "CA"),
    (1, "AAA", "CCA", 1, "AAA", "CCA"),
    (1, "AAA", "ACA", 2, "AA", "CA"),
    (100, "TGGTGCAGGC", "T", 101, "GGTGCAGGC", ""),
    (100, "TGGTGCAGGC", "CGGTGCAGGC", 100, "TGGTGCAGGC", "CGGTGCAGGC"),
    (100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC", 110, "", "GGTGCAGGC"),
    (100, "TGGTGCAGGC", "TGGTGCAGGT", 109, "C", "T"),
])
def test_trim_str_left(pos, ref, alt, trim_pos, trim_ref, trim_alt):

    tpos, tref, talt = trim_str_left(pos, ref, alt)
    assert trim_pos == tpos
    assert trim_ref == tref
    assert trim_alt == talt


@pytest.mark.parametrize("allele,parsimonious", [
    ((1, "AA", "CA"), (1, "A", "C")),
    ((1, "CA", "CT"), (2, "A", "T")),
    ((1, "ACA", "A"), (1, "ACA", "A")),
    ((1, "AACA", "AA"), (1, "AAC", "A")),
    ((4, "GCAT", "GTGC"), (5, "CAT", "TGC")),
    ((5, "CATG", "TGCG"), (5, "CAT", "TGC")),
    ((4, "GCATG", "GTGCG"), (5, "CAT", "TGC")),
    ((4, "GG", "GAGG"), (4, "G", "GAG")),
    ((100, "TGGTGCAGGC", "T"), (100, "TGGTGCAGGC", "T")),
    ((100, "TGGTGCAGGC", "CGGTGCAGGC"), (100, "T", "C")),
    ((100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC"), (100, "T", "TGGTGCAGGC")),
    ((100, "TGGTGCAGGC", "TGGTGCAGGT"), (109, "C", "T")),
])
def test_trim_parsimonious(allele, parsimonious):
    pos, ref, alt = trim_parsimonious(*allele)

    assert (pos, ref, alt) == parsimonious
