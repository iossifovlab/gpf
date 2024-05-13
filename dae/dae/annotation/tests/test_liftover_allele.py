# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme
import textwrap

import pytest

from dae.annotation.liftover_annotator import (
    liftover_allele,
    liftover_variant,
)
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
)
from dae.genomic_resources.variant_utils import (
    maximally_extend_variant,
)
from dae.utils.variant_utils import reverse_complement


@pytest.mark.parametrize("chrom,pos,ref,alt,echrom, epos,eref,ealt", [
    ("foo", 6, "C", "G", "chrFoo", 2, "C", "G"),
    ("foo", 5, "A", "C", "chrFoo", 1, "A", "C"),
])
def test_liftover_allele_util(
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    echrom: str,
    epos: int,
    eref: str,
    ealt: str,
    liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    res = liftover_grr_fixture.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res).open()
    assert liftover_chain is not None

    res = liftover_grr_fixture.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res).open()
    assert source_genome is not None
    res = liftover_grr_fixture.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res).open()
    assert target_genome is not None

    lresult = liftover_allele(
        chrom, pos, ref, alt,
        liftover_chain, source_genome, target_genome,
    )

    assert lresult is not None
    lchrom, lpos, lref, lalt = lresult

    assert lchrom == echrom
    assert lpos == epos
    assert lref == eref
    assert lalt == ealt


@pytest.fixture()
def liftover_ex4_grr(
        tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("liftover_ex4_grr")
    setup_directories(root_path, {
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "source_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "liftover_chain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain

                filename: liftover.chain.gz
            """),
        },
    })
    #
    # The initial header line starts with the keyword chain, followed
    # by 11 required attribute values, and ends with a blank line.
    #
    # The attributes include:
    #
    # score -- chain score
    # tName -- chromosome (reference/target sequence); source contig;
    # tSize -- chromosome size (reference/target sequence); full length of the
    #          source chromosome;
    # tStrand -- strand (reference/target sequence); must be +
    # tStart -- alignment start position (reference/target sequence);
    #           Start of source region
    # tEnd -- alignment end position (reference/target sequence);
    #         End of source region
    # qName -- chromosome (query sequence); target chromosome name;
    # qSize -- chromosome size (query sequence); Full length of the chromosome
    # qStrand -- strand (query sequence); + or -
    # qStart -- alignment start position (query sequence); target start;
    # qEnd -- alignment end position (query sequence); target end;
    # id -- chain ID
    #
    # Block format:
    # Alignment data lines contain three required attribute values:

    # size dt dq
    # size -- the size of the ungapped alignment
    # dt -- the difference between the end of this block and the beginning
    #       of the next block (reference/target sequence)
    # dq -- the difference between the end of this block and the beginning
    #       of the next block (query sequence)
    #
    # The last line of the alignment section contains only one number: the
    # ungapped alignment size of the last block.
    #
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 2200 22 40 + 20 40 chr22 20 + 0 20 4a
        20 0 0
        0

        chain 1800 18 40 + 20 40 chr18 20 + 0 20 4b
        20 0 0
        0

        chain 2300 X 40 + 20 40 chrX 20 + 0 20 4c
        20 0 0
        0

        chain 2100 21 40 + 20 39 chr21 20 + 0 20 4d
        9 1 2
        9 0 0
        0

        """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent("""
            >22
            NNNNNNNNNNNNNNNNNNNN
            NNNATAAAGACATAAANNNN
            #  ATAAAGGCATAAA
            >18
            NNNNNNNNNNNNNNNNNNNN
            NNAATTGGCGATGTTTCTTG
            >X
            NNNNNNNNNNNNNNNNNNNN
            NNNGTGAGACTTATCTANNN
            >21
            NNNNNNNNNNNNNNNNNNNN
            NNNTTCTTTCTTTTTTNNNN
            """),
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent("""
            >chr22
            NNNATAAAGGCATAAANNNN
            >chr18
            NNAATTGGTGATGCTTCTTG
            >chrX
            NNNGTGAGATTTATCTANNN
            >chr21
            NNNNTTCTTTTTTTTTTTNN
            """),
    )

    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("schrom,spos,sref,tchrom,tpos,tref,strand,qual", [
    ("22", 30, "A", "chr22", 10, "G", "+", 2200),
    ("18", 29, "C", "chr18", 9, "T", "+", 1800),
    ("X", 30, "C", "chrX", 10, "T", "+", 2300),
])
def test_ex4_fixture(
    liftover_ex4_grr: GenomicResourceRepo,
    schrom: str, spos: int, sref: str,
    tchrom: str, tpos: int, tref: str,
    strand: str, qual: int,
) -> None:

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)

    assert target_genome is not None
    assert source_genome is not None
    assert liftover_chain is not None

    liftover_chain.open()
    source_genome.open()
    target_genome.open()

    s_seq = source_genome.get_sequence(schrom, spos, spos)
    assert s_seq == sref
    t_seq = target_genome.get_sequence(tchrom, tpos, tpos)
    assert t_seq == tref

    lo_coordinates = liftover_chain.convert_coordinate(schrom, spos)
    assert lo_coordinates is not None
    assert lo_coordinates == (tchrom, tpos, strand, qual)


def test_ex4d_fixture(
    liftover_ex4_grr: GenomicResourceRepo,
) -> None:

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)

    assert target_genome is not None
    assert source_genome is not None
    assert liftover_chain is not None

    liftover_chain.open()
    source_genome.open()
    target_genome.open()

    s_ref = source_genome.get_sequence("21", 30, 30)
    assert s_ref == "C"
    t_ref = target_genome.get_sequence("chr21", 10, 10)
    assert t_ref == "T"

    lo_coordinates = liftover_chain.convert_coordinate("21", 30)
    assert lo_coordinates is None
    lo_start = liftover_chain.convert_coordinate("21", 30 - 1)
    assert lo_start is not None
    lo_end = liftover_chain.convert_coordinate("21", 30 + 1)
    assert lo_end is not None

    chrom, start_pos, strand, qual = lo_start
    assert chrom == "chr21"
    assert start_pos == 9
    assert strand == "+"
    assert qual == 2100

    chrom, end_pos, strand, qual = lo_end
    assert chrom == "chr21"
    assert end_pos == 12
    assert strand == "+"
    assert qual == 2100

    t_ref = target_genome.get_sequence("chr21", start_pos, end_pos)
    assert t_ref == "TTTT"


@pytest.fixture()
def liftover_ex3_grr(
        tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("liftover_ex4_grr")
    setup_directories(root_path, {
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "source_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "liftover_chain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain

                filename: liftover.chain.gz
            """),
        },
    })
    #
    # The initial header line starts with the keyword chain, followed
    # by 11 required attribute values, and ends with a blank line.
    #
    # The attributes include:
    #
    # score -- chain score
    # tName -- chromosome (reference/target sequence); source contig;
    # tSize -- chromosome size (reference/target sequence); full length of the
    #          source chromosome;
    # tStrand -- strand (reference/target sequence); must be +
    # tStart -- alignment start position (reference/target sequence);
    #           Start of source region
    # tEnd -- alignment end position (reference/target sequence);
    #         End of source region
    # qName -- chromosome (query sequence); target chromosome name;
    # qSize -- chromosome size (query sequence); Full length of the chromosome
    # qStrand -- strand (query sequence); + or -
    # qStart -- alignment start position (query sequence); target start;
    # qEnd -- alignment end position (query sequence); target end;
    # id -- chain ID
    #
    # Block format:
    # Alignment data lines contain three required attribute values:

    # size dt dq
    # size -- the size of the ungapped alignment
    # dt -- the difference between the end of this block and the beginning
    #       of the next block (reference/target sequence)
    # dq -- the difference between the end of this block and the beginning
    #       of the next block (query sequence)
    #
    # The last line of the alignment section contains only one number: the
    # ungapped alignment size of the last block.
    #
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 1000 10 60 + 30 55 chr10 30 - 5 30 3a
        25 0 0
        0

        """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent("""
            >10
            NNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
            NNNGCCTAAGATAATAATTGCTGGNNNNNN
            """),
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent("""
            >chr10
            NNNNCCAGCAATTATCTTAGGNNNNNNNNN
            """),
    )

    return build_filesystem_test_repository(root_path)


def test_ex3a_fixture(
    liftover_ex3_grr: GenomicResourceRepo,
) -> None:

    res = liftover_ex3_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    res = liftover_ex3_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    res = liftover_ex3_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)

    assert target_genome is not None
    assert source_genome is not None
    assert liftover_chain is not None

    liftover_chain.open()
    source_genome.open()
    target_genome.open()

    assert source_genome.get_sequence("10", 40, 40) == "G"
    assert target_genome.get_sequence("chr10", 19, 19) == "A"

    t_seq = target_genome.get_sequence("chr10", 10, 10 + 6)
    assert t_seq == "AATTATC"
    assert reverse_complement(t_seq) == "GATAATT"

    lo_coordinates = liftover_chain.convert_coordinate("10", 40)
    assert lo_coordinates is not None
    chrom, pos, strand, qual = lo_coordinates
    assert strand == "-"
    assert qual == 1000
    assert chrom == "chr10"
    assert pos == 16

    assert source_genome.get_sequence("10", 40 + 8, 40 + 8) == "T"
    assert target_genome.get_sequence("chr10", 10 + 6, 10 + 6) == "C"

    lo_coordinates = liftover_chain.convert_coordinate("10", 40 + 6)
    assert lo_coordinates is not None
    chrom, pos, strand, qual = lo_coordinates
    assert strand == "-"
    assert qual == 1000
    assert chrom == "chr10"
    assert pos == 10

    t_seq = target_genome.get_sequence("chr10", 10, 16)
    assert t_seq == "AATTATC"
    assert reverse_complement(t_seq) == "GATAATT"


def test_ex3a_liftover_parts(
    liftover_ex3_grr: GenomicResourceRepo,
) -> None:
    res = liftover_ex3_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)
    source_genome.open()

    res = liftover_ex3_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    target_genome.open()

    res = liftover_ex3_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)
    liftover_chain.open()

    mchrom, mpos, mref, malts = maximally_extend_variant(
        "10", 40, "GATA", ["G"], source_genome,
    )
    assert mchrom == "10"
    assert mpos == 40
    assert mref == "GATAATAATT"
    assert malts == ["GATAATT"]

    result = liftover_allele(
        "10", 40, "GATA", "G",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr10"
    assert lpos == 10
    assert lref == "A"
    assert lalt == "AATT"


def test_ex4a_liftover_parts(
    liftover_ex4_grr: GenomicResourceRepo,
) -> None:
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)
    source_genome.open()

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    target_genome.open()

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)
    liftover_chain.open()

    mchrom, mpos, mref, malts = maximally_extend_variant(
        "22", 30, "A", ["G"], source_genome,
    )
    assert mchrom == "22"
    assert mpos == 29
    assert mref == "GAC"
    assert malts == ["GGC"]

    result = liftover_allele(
        "22", 30, "A", "G",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr22"
    assert lpos == 10
    assert lref == "G"
    assert lalt == "A"


def test_ex4a_liftover_variant(
    liftover_ex4_grr: GenomicResourceRepo,
) -> None:
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)
    source_genome.open()

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    target_genome.open()

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)
    liftover_chain.open()

    result = liftover_allele(
        "22", 25, "TAA", "T",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr22"
    assert lpos == 5
    assert lref == "TAA"
    assert lalt == "T"

    result = liftover_allele(
        "22", 25, "T", "G",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr22"
    assert lpos == 5
    assert lref == "T"
    assert lalt == "G"

    # 1:47173530 CCAAA > TCAAA,C
    # 22:25 TAA > CAA,T
    result = liftover_allele(
        "22", 25, "TAA", "CAA",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr22"
    assert lpos == 5
    assert lref == "T"
    assert lalt == "C"

    result = liftover_allele(
        "22", 25, "TAA", "C",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr22"
    assert lpos == 5
    assert lref == "TAA"
    assert lalt == "C"

    r_variant = liftover_variant(
        "22", 25, "TAA", ["CAA", "C"],
        liftover_chain, source_genome, target_genome)
    assert r_variant is not None

    lchrom, lpos, lref, lalts = r_variant
    assert lchrom == "chr22"
    assert lpos == 5
    assert lref == "TAA"
    assert lalts == ["CAA", "C"]


def test_ex4b_liftover_parts(
    liftover_ex4_grr: GenomicResourceRepo,
) -> None:
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)
    source_genome.open()

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    target_genome.open()

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)
    liftover_chain.open()

    mchrom, mpos, mref, malts = maximally_extend_variant(
        "18", 29, "C", ["T"], source_genome,
    )
    assert mchrom == "18"
    assert mpos == 28
    assert mref == "GCG"
    assert malts == ["GTG"]

    result = liftover_allele(
        "18", 29, "C", "T",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chr18"
    assert lpos == 9
    assert lref == "T"
    assert lalt == "C"


def test_ex4c_liftover_parts(
    liftover_ex4_grr: GenomicResourceRepo,
) -> None:
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)
    source_genome.open()

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    target_genome.open()

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)
    liftover_chain.open()

    mchrom, mpos, mref, malts = maximally_extend_variant(
        "X", 30, "C", ["T"], source_genome,
    )
    assert mchrom == "X"
    assert mpos == 29
    assert mref == "ACT"
    assert malts == ["ATT"]

    result = liftover_allele(
        "X", 30, "C", "T",
        liftover_chain, source_genome, target_genome)
    assert result is not None

    lchrom, lpos, lref, lalt = result
    assert lchrom == "chrX"
    assert lpos == 10
    assert lref == "T"
    assert lalt == "C"


def test_ex4d_liftover_parts(
    liftover_ex4_grr: GenomicResourceRepo,
) -> None:
    res = liftover_ex4_grr.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res)
    source_genome.open()

    res = liftover_ex4_grr.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res)
    target_genome.open()

    res = liftover_ex4_grr.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)
    liftover_chain.open()

    mchrom, mpos, mref, malts = maximally_extend_variant(
        "21", 30, "C", ["T"], source_genome,
    )
    assert mchrom == "21"
    assert mpos == 29
    assert mref == "TCT"
    assert malts == ["TTT"]

    result = liftover_allele(
        "21", 30, "C", "T",
        liftover_chain, source_genome, target_genome)
    assert result is None
