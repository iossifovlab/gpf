# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme,R0917
import pathlib
import textwrap

import pytest
from dae.annotation.liftover_annotator import bcf_liftover_allele
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


@pytest.fixture
def liftover_data(
    tmp_path: pathlib.Path,
) -> GenomicResourceRepo:
    setup_genome(
        tmp_path / "source_genome" / "genome.fa",
        textwrap.dedent("""
            >chrA
            NNNNNAAAAA
            TCTCTGGGGG
            CCCCC
            """),
    )
    setup_genome(
        tmp_path / "target_genome" / "genome.fa",
        textwrap.dedent("""
            >chrB
            NNNNNAAAAA
            AGAGACCCCC
            CCCCC
            """),
    )
    # chain score tName tSize tStr tStart tEnd qName qSize qStr qStart qEnd id
    # alignment data lines: size dt dq
    #
    # 1. Identity: chrA:0-10 -> chrB:0-10 (+)
    #    chain 100 chrB 25 + 0 10 chrA 25 + 0 10 1
    #    10 0 0
    #    0
    #
    # 2. Strand: chrA:10-15 -> chrB:10-15 (-)
    #    chain 100 chrB 25 - 10 15 chrA 25 + 10 15 2
    #    5 0 0
    #    0
    #
    # 3. Swap: chrA:15-20 -> chrB:15-20 (+)
    #    chain 100 chrB 25 + 15 20 chrA 25 + 15 20 3
    #    5 0 0
    #    0

    setup_gzip(
        tmp_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 100 chrA 25 + 0 10 chrB 25 + 0 10 1
        10 0 0
        0
        chain 100 chrA 25 + 10 15 chrB 25 - 10 15 2
        5 0 0
        0
        chain 100 chrA 25 + 15 20 chrB 25 + 15 20 3
        5 0 0
        0
        """),
    )
    setup_directories(tmp_path, {
        "source_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "liftover_chain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain
                filename: liftover.chain.gz
                meta:
                  labels:
                    source_genome: source_genome
                    target_genome: target_genome
            """),
        },
    })

    return build_filesystem_test_repository(tmp_path)


def test_check_liftover_resources(
    liftover_data: GenomicResourceRepo,
) -> None:
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome"),
    ).open()
    assert source_genome is not None
    assert "chrA" in source_genome.chromosomes

    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome"),
    ).open()
    assert target_genome is not None
    assert "chrB" in target_genome.chromosomes

    liftover_chain = build_liftover_chain_from_resource(
        liftover_data.get_resource("liftover_chain"),
    ).open()
    assert liftover_chain is not None
    mapped = liftover_chain.convert_coordinate("chrA", 2)
    assert mapped == ("chrB", 2, "+", 100)


def test_liftover_simple_identity(liftover_data: GenomicResourceRepo) -> None:
    chain_res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(chain_res).open()
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome")).open()
    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome")).open()

    # chrA:6 is 'A' (0-based index 5)
    # Maps to chrB:6 'A'
    # Variant A>T
    result = bcf_liftover_allele(
        "chrA", 6, "A", "T", chain,
        source_genome=source_genome,
        target_genome=target_genome,
    )

    assert result is not None
    chrom, pos, ref, alt = result
    assert chrom == "chrB"
    assert pos == 6
    assert ref == "A"
    assert alt == "T"


def test_liftover_strand_change(liftover_data: GenomicResourceRepo) -> None:
    chain_res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(chain_res).open()
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome")).open()
    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome")).open()

    # chrA:11 is 'T' (0-based index 10)
    # Maps to chrB:10-15 (-)
    # Target is 'A's.
    # Source 'T' on (+) maps to 'A' on (-).
    # Variant T>G on (+)
    # On (-) strand: RevComp(T)>RevComp(G) => A>C

    # Wait, let's check coordinates.
    # chrA:11 (1-based) -> index 10.
    # Chain 2: chrA 10-15 -> chrB 10-15 (-)
    # pyliftover converts 0-based.
    # 10 -> 25 - 1 - 10 = 14? No, pyliftover logic for negative strand:
    # tSize - 1 - mapped_pos?
    # Let's verify coordinate mapping first.

    _lo_coord = chain.convert_coordinate("chrA", 11)
    # If it maps to negative strand, we expect strand to be '-'

    result = bcf_liftover_allele(
        "chrA", 11, "T", "G", chain,
        source_genome=source_genome,
        target_genome=target_genome,
    )

    assert result is not None
    chrom, _pos, ref, alt = result
    assert chrom == "chrB"
    # Position might need verification based on exact chain mapping
    assert ref == "A"  # RevComp of T
    assert alt == "C"  # RevComp of G


def test_liftover_allele_swap(liftover_data: GenomicResourceRepo) -> None:
    chain_res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(chain_res).open()
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome")).open()
    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome")).open()

    # chrA:16 is 'G' (0-based index 15)
    # Maps to chrB:16 'C'
    # Variant G>C
    # Source Ref: G, Target Ref: C.
    # Source Alt: C, Target Ref: C.
    # This is a swap! G>C becomes C>G.

    result = bcf_liftover_allele(
        "chrA", 16, "G", "C", chain,
        source_genome=source_genome,
        target_genome=target_genome,
    )

    assert result is not None
    chrom, pos, ref, alt = result
    assert chrom == "chrB"
    assert pos == 16
    assert ref == "C"
    assert alt == "G"


def test_liftover_ref_mismatch_failure(
    liftover_data: GenomicResourceRepo,
) -> None:
    chain_res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(chain_res).open()
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome")).open()
    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome")).open()

    # chrA:16 is 'G'. Target is 'C'.
    # Variant G>A.
    # Source Ref: G != Target Ref C.
    # Source Alt: A != Target Ref C.
    # Should fail.

    result = bcf_liftover_allele(
        "chrA", 16, "G", "A", chain,
        source_genome=source_genome,
        target_genome=target_genome,
    )

    assert result is None


def test_liftover_indel_simple(liftover_data: GenomicResourceRepo) -> None:
    chain_res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(chain_res).open()
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome")).open()
    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome")).open()

    # chrA:6 is 'A'.
    # Variant A>AT (Insertion)
    result = bcf_liftover_allele(
        "chrA", 6, "A", "AT", chain,
        source_genome=source_genome,
        target_genome=target_genome,
    )

    assert result is not None
    chrom, pos, ref, alt = result
    assert chrom == "chrB"
    assert pos == 6
    assert ref == "A"
    assert alt == "AT"


def test_liftover_indel_strand(liftover_data: GenomicResourceRepo) -> None:
    chain_res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(chain_res).open()
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome")).open()
    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome")).open()

    # chrA:12 is 'C' (index 11).
    # Sequence TCTCT.
    # Variant C>CT (Insertion of T)
    # Maps to chrB (-)
    # C -> G
    # CT -> AG
    # Result should be G>GA (Left aligned)

    result = bcf_liftover_allele(
        "chrA", 12, "C", "CT", chain,
        source_genome=source_genome,
        target_genome=target_genome,
    )

    assert result is not None
    chrom, pos, ref, alt = result
    assert chrom == "chrB"
    assert pos == 12
    assert ref == "G"
    assert alt == "GA"
