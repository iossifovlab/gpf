# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import numpy as np
import pytest

from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    setup_directories,
)
from dae.utils.variant_utils import (
    get_locus_ploidy,
    gt2str,
    reverse_complement,
    str2gt,
    trim_parsimonious,
    trim_str_left,
    trim_str_right,
)
from dae.variants.attributes import Sex


@pytest.fixture()
def genome(tmp_path: pathlib.Path) -> ReferenceGenome:
    root_path = tmp_path
    setup_directories(root_path, {
        GR_CONF_FILE_NAME: """
            type: genome
            filename: chr.fa
            PARS:
                X:
                    - "X:10000-2781479"
                    - "X:155701382-156030895"
                Y:
                    - "Y:10000-2781479"
                    - "Y:56887902-57217415"
        """,
        "chr.fa": textwrap.dedent("""
            >pesho
            NGNACCCAAAC
            GGGCCTTCCN
            NNNA
            >gosho
            NNAACCGGTT
            TTGCCAANN"""),
        "chr.fa.fai": "pesho\t24\t8\t10\t11\ngosho\t20\t42\t10\t11",
    })
    res = build_filesystem_test_resource(root_path)
    return build_reference_genome_from_resource(res)


chroms: list[int | str] = list(range(1, 23))
chroms.append("Y")

test_data = [
    (str(chrom), 50, sex, 2)
    for sex in (Sex.M, Sex.F)
    for chrom in list(range(1, 23))
]

test_data.extend(
    (
        ("X", 500, Sex.M, 1),
        ("X", 10000, Sex.M, 2),
        ("X", 105000, Sex.M, 2),
        ("X", 2781479, Sex.M, 2),
        ("X", 3000000, Sex.M, 1),
        ("X", 155700000, Sex.M, 1),
        ("X", 155701382, Sex.M, 2),
        ("X", 156000000, Sex.M, 2),
        ("X", 156030895, Sex.M, 2),
        ("X", 200000000, Sex.M, 1),
        ("Y", 500, Sex.M, 1),
        ("Y", 10000, Sex.M, 2),
        ("Y", 105000, Sex.M, 2),
        ("Y", 2781479, Sex.M, 2),
        ("Y", 3000000, Sex.M, 1),
        ("Y", 56800000, Sex.M, 1),
        ("Y", 56887902, Sex.M, 2),
        ("Y", 56900000, Sex.M, 2),
        ("Y", 57000000, Sex.M, 2),
        ("Y", 57217415, Sex.M, 2),
        ("Y", 60000000, Sex.M, 1),
        ("X", 500, Sex.U, 1),
        ("X", 10000, Sex.U, 2),
        ("X", 105000, Sex.U, 2),
        ("X", 2781479, Sex.U, 2),
        ("X", 3000000, Sex.U, 1),
        ("X", 155700000, Sex.U, 1),
        ("X", 155701382, Sex.U, 2),
        ("X", 156000000, Sex.U, 2),
        ("X", 156030895, Sex.U, 2),
        ("X", 200000000, Sex.U, 1),
        ("Y", 500, Sex.U, 1),
        ("Y", 10000, Sex.U, 2),
        ("Y", 105000, Sex.U, 2),
        ("Y", 2781479, Sex.U, 2),
        ("Y", 3000000, Sex.U, 1),
        ("Y", 56800000, Sex.U, 1),
        ("Y", 56887902, Sex.U, 2),
        ("Y", 56900000, Sex.U, 2),
        ("Y", 57000000, Sex.U, 2),
        ("Y", 57217415, Sex.U, 2),
        ("Y", 60000000, Sex.U, 1),
        ("X", 500, Sex.F, 2),
        ("X", 155701382, Sex.F, 2),
        ("X", 2781479, Sex.F, 2),
        ("X", 156030895, Sex.F, 2),
        ("X", 57217415, Sex.F, 2),
    ),
)

# test_data_chr_prefix = list(
#     map(lambda x: ("chr" + x[0], x[1], x[2], x[3]), test_data)
# )
# test_data.extend(test_data_chr_prefix)


@pytest.mark.parametrize("chrom,pos,sex,expected", [*test_data])
def test_get_locus_ploidy(
    genome: ReferenceGenome,
    chrom: str,
    pos: int,
    sex: Sex,
    expected: int,
) -> None:
    assert get_locus_ploidy(chrom, pos, sex, genome) == expected


def test_get_locus_ploidy_y_chrom_female(genome: ReferenceGenome) -> None:
    with pytest.raises(
        ValueError, match="Chromosome Y identified for a female individual!"):
        get_locus_ploidy("Y", 57217415, Sex.F, genome)


@pytest.mark.parametrize("dna,expected", [
    ("a", "T"),
    ("ac", "GT"),
    ("actg", "CAGT"),
])
def test_reverse_complement(dna: str, expected: str) -> None:
    result = reverse_complement(dna)
    assert result == expected


@pytest.mark.parametrize("gt,expected", [
    (
        np.array([[0, 0, 0], [0, 1, 0]], dtype=np.int8),
        "0/0,0/1,0/0",
    ),
    (
        np.array([[0, 0, 0], [0, -1, 0]], dtype=np.int8),
        "0/0,0/.,0/0",
    ),
    (
        np.array([[0, 1, 0], [0, -1, 0]], dtype=np.int8),
        "0/0,1/.,0/0",
    ),
])
def test_gt2str(gt: np.ndarray, expected: np.ndarray) -> None:
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
def test_str2gt(gts: str, expected: np.ndarray) -> None:
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
def test_trim_str_right(
    pos: int,
    ref: str,
    alt: str,
    trim_pos: int,
    trim_ref: str,
    trim_alt: str,
) -> None:
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
def test_trim_str_left(
    pos: int,
    ref: str,
    alt: str,
    trim_pos: int,
    trim_ref: str,
    trim_alt: str,
) -> None:
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
def test_trim_parsimonious(
    allele: tuple[int, str, str], parsimonious: tuple[int, str, str]) -> None:
    pos, ref, alt = trim_parsimonious(*allele)

    assert (pos, ref, alt) == parsimonious
