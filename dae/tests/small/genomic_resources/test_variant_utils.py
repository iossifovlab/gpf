# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.variant_utils import (
    maximally_extend_variant,
    normalize_variant,
)


@pytest.mark.parametrize("beg,end,seq", [
    (1, 11, "GGGGCATGGGG"),
    (4, 7, "GCAT"),
    (5, 8, "CATG"),
    (4, 8, "GCATG"),
    (5, 7, "CAT"),
])
def test_normalize_genome_1_basic(
        normalize_genome_1: ReferenceGenome,
        beg: int, end: int, seq: str) -> None:
    with normalize_genome_1.open() as genome:
        assert genome.get_chrom_length("1") == 11

        assert genome.get_sequence("1", beg, end) == seq


@pytest.mark.parametrize("beg,end,seq", [
    (1, 14, "GGGCACACACAGGG"),
    (8, 9, "CA"),
    (6, 8, "CAC"),
    (3, 7, "GCACA"),
    (2, 5, "GGCA"),
    (3, 5, "GCA"),
    (3, 3, "G"),
])
def test_noramalize_genome_basic_2(
        normalize_genome_2: ReferenceGenome,
        beg: int, end: int, seq: str) -> None:
    with normalize_genome_2.open() as genome:
        assert genome.get_chrom_length("1") == 14

        assert genome.get_sequence("1", beg, end) == seq


@pytest.mark.parametrize("pos,ref,alt", [
    (4, "GCAT", "GTGC"),
    (5, "CATG", "TGCG"),
    (4, "GCATG", "GTGCG"),
    (5, "CAT", "TGC"),
])
def test_example_1_normalize(
        normalize_genome_1: ReferenceGenome,
        pos: int, ref: str, alt: str) -> None:
    with normalize_genome_1.open() as genome:
        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        nchrom, npos, nref, nalts = \
            normalize_variant("1", pos, ref, [alt], genome)

        assert nchrom == "1"
        assert npos == 5
        assert nref == "CAT"
        assert nalts == ["TGC"]


@pytest.mark.parametrize("pos,ref,alt", [
    (8, "CA", ""),
    (6, "CAC", "C"),
    (3, "GCACA", "GCA"),
    (2, "GGCA", "GG"),
    (3, "GCA", "G"),
])
def test_example_2_normalize(
        normalize_genome_2: ReferenceGenome,
        pos: int, ref: str, alt: str) -> None:

    with normalize_genome_2.open() as genome:
        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        nchrom, npos, nref, nalts = \
            normalize_variant("1", pos, ref, [alt], genome)

        assert nchrom == "1"
        assert npos == 3
        assert nref == "GCA"
        assert nalts == ["G"]


@pytest.mark.parametrize("pos,ref,alts", [
    (1, "GGGCA", ["GGG", "GGCCA"]),
    (2, "GGCA", ["GG", "GCCA"]),
    (3, "GCA", ["G", "CCA"]),
])
def test_example_2_normalize_variant(
        normalize_genome_2: ReferenceGenome,
        pos: int, ref: str, alts: list[str]) -> None:

    with normalize_genome_2.open() as genome:
        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        nchrom, npos, nref, nalts = normalize_variant(
            "1", pos, ref, alts, genome)

        assert nchrom == "1"
        assert len(nalts) == 2
        assert nref == "GCA"
        assert npos == 3

        assert nalts == ["G", "CCA"]


@pytest.mark.parametrize("pos,ref,alt", [
    (8, "CA", ""),
    (6, "CAC", "C"),
    (3, "GCACA", "GCA"),
    (2, "GGCA", "GG"),
    (3, "GCA", "G"),
])
def test_example_2_maximally_extend_variant(
        normalize_genome_2: ReferenceGenome,
        pos: int, ref: str, alt: str) -> None:

    with normalize_genome_2.open() as genome:
        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        mchrom, mpos, mref, malts = maximally_extend_variant(
            "1", pos, ref, [alt], genome)

        assert mchrom
        assert mpos == 3
        assert mref == "GCACACACAG"
        assert malts[0] == "GCACACAG"


@pytest.mark.parametrize("pos,ref,alt,epos, eref, ealt", [
    (8, "C", "C", 8, "C", "C"),
    (1, "G", "G", 1, "G", "G"),
    (1, "GGGCA", "GGGCA", 1, "G", "G"),
    (4, "CA", "CA", 4, "C", "C"),
])
def test_normalize_novariant_allele(
        normalize_genome_2: ReferenceGenome,
        pos: int, ref: str, alt: str,
        epos: int, eref: str, ealt: str) -> None:
    with normalize_genome_2.open() as genome:

        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        nchrom, npos, nref, nalts = \
            normalize_variant("1", pos, ref, [alt], genome)

        assert nchrom == "1"
        assert npos == epos
        assert nref == eref
        assert nalts == [ealt]


@pytest.mark.parametrize("chrom,pos,ref,alts,epos,eref,ealts", [
    ("foo", 6, "C", ["G"], 5, "ACG", ["AGG"]),
    ("foo", 7, "G", ["T", "A"], 6, "CGT", ["CTT", "CAT"]),
    ("foo", 9, "A", ["T", "AA"], 8, "TAC", ["TTC", "TAAC"]),
    ("foo", 93, "A", ["ACGTACGTACGT"],
     93, "ACGTACGTACGT", ["ACGTACGTACGTCGTACGTACGT"]),
])
def test_maximally_extend_variant(
    chrom: str,
    pos: int,
    ref: str,
    alts: list[str],
    epos: int,
    eref: str,
    ealts: list[str],
    liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    res = liftover_grr_fixture.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res).open()
    assert source_genome is not None

    chec_ref = source_genome.get_sequence(chrom, pos, pos)
    assert chec_ref == ref

    mchrom, mpos, mref, malts = maximally_extend_variant(
        chrom, pos, ref, alts, source_genome)
    assert mchrom == chrom
    assert mpos == epos
    assert mref == eref
    assert malts == ealts
