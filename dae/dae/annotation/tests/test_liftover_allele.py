# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme
import textwrap

import pytest

from dae.annotation.liftover_annotator import (
    liftover_allele,
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
    lchrom, lpos, lref, lalts = lresult

    assert lchrom == echrom
    assert lpos == epos
    assert lref == eref
    assert lalts == [ealt]


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
        chain 4900 22 40 + 20 40 chr22 20 + 0 20 4a
        20 0 0
        0

        """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent("""
            >22
            NNNNNNNNNNNNNNNNNNNN
            NNNATAAAGACATAAANNNN
            """),
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent("""
            >chr22
            NNNATAAAGGCATAAANNNN
            """),
    )

    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("schrom,spos,sref,tchrom,tpos,tref,strand,qual", [
    ("22", 30, "A", "chr22", 10, "G", "+", 4900),
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
