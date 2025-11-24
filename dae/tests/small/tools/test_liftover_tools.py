# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme
import pathlib
import textwrap
from contextlib import closing

import pysam
import pytest
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_dae_transmitted,
    setup_directories,
    setup_genome,
    setup_gzip,
    setup_pedigree,
    setup_vcf,
)
from dae.tools.dae_liftover import main as dae_liftover_main
from dae.tools.vcf_liftover import main


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


@pytest.fixture
def liftover_gap_data(
    tmp_path: pathlib.Path,
) -> GenomicResourceRepo:
    setup_genome(
        tmp_path / "source_genome" / "genome.fa",
        textwrap.dedent("""
            >chrA
            NNNNNAAAAA
            GGGGGTTTTT
            CCCCC
            """),
    )
    setup_genome(
        tmp_path / "target_genome" / "genome.fa",
        textwrap.dedent("""
            >chrB
            NNNNNAAAAA
            TTTTTCCCCC
            CCCCC
            """),
    )
    # Chain with a gap in source.
    # chrA:0-10 maps to chrB:0-10
    # Gap in chrA of 5 bases (10-15).
    # chrA:15-20 maps to chrB:10-15.
    #
    # Chain header:
    # chain 100 chrA 25 + 0 20 chrB 25 + 0 15 1
    # Block 1: size 10.
    # dt = 5 (source skips 5 bases: 10-15)
    # dq = 0 (target continues)
    # Block 2: size 5.
    #
    # 10 5 0
    # 5

    setup_gzip(
        tmp_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 100 chrA 25 + 0 20 chrB 25 + 0 15 1
        10 5 0
        5
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


def test_vcf_liftover_identity(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    # Identity region: chrA:0-10 -> chrB:0-10 (+)
    # Variant at chrA:6 A->C should map to chrB:6 A->C
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   6   .  A   C   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_data)

    assert out_vcf.with_suffix(".vcf").exists()

    with closing(pysam.VariantFile(
            str(out_vcf.with_suffix(".vcf")))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 1
        v = variants[0]
        assert v.chrom == "chrB"
        assert v.pos == 6
        assert v.ref == "A"
        assert v.alts == ("C",)


def test_vcf_liftover_strand_change(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    # Strand region: chrA:10-15 -> chrB:10-15 (-)
    # where chrA:10-15 is TCTCT
    # mapped to chrB:10-15 is AGAGA (reverse complement of TCTCT)
    # Variant at chrA:13 T->G
    # On negative strand, T->G becomes A->C
    # Position:
    # chrA:10 -> chrB:15 (index 14)
    # chrA:11 -> chrB:14 (index 13)
    # chrA:12 -> chrB:13 (index 12)
    # chrA:13 -> chrB:12 (index 11)
    # So pos should be 12 (1-based)

    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   13  .  T   G   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_data)

    with closing(pysam.VariantFile(
            str(out_vcf.with_suffix(".vcf")))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 1
        v = variants[0]
        assert v.chrom == "chrB"
        assert v.pos == 13
        assert v.ref == "A"
        assert v.alts == ("C",)


def test_vcf_liftover_allele_swap(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    # Swap region: chrA:15-20 -> chrB:15-20 (+)
    # where chrA:15-20 is GGGGG
    # mapped to chrB:15-20 is CCCCC
    # Variant at chrA:16 G->C
    # Target ref is C.
    # Source ref G matches target alt C.
    # Source alt C matches target ref C.
    # So this is a reference mismatch that looks like a swap.
    # The tool should detect this and swap alleles if configured?
    # Wait, standard liftover usually drops if ref doesn't match.
    # But let's see what happens.
    # In test_liftover_extended.py we saw that it returns None
    # for simple liftover if ref mismatch.
    # But if we have a variant G->C and target ref is C, maybe it becomes C->G?

    # Let's try a case where it works.
    # chrA:16 G -> C.
    # Target ref at 16 is C.
    # If we map G->C to target, we expect Ref=C.
    # If we just map coordinates, we get pos 16.
    # If we check ref, we see C.
    # Input ref G != Target ref C.
    # Input alt C == Target ref C.
    # So we can swap: C -> G.

    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   16  .  G   C   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_data)

    with closing(pysam.VariantFile(
            str(out_vcf.with_suffix(".vcf")))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 1
        v = variants[0]
        assert v.chrom == "chrB"
        assert v.pos == 16
        assert v.ref == "C"
        assert v.alts == ("G",)


def test_vcf_liftover_chain_gap(
    tmp_path: pathlib.Path,
    liftover_gap_data: GenomicResourceRepo,
) -> None:
    # Chain gap region: chrA:10-15 is a gap in source.
    # chrA:12 is in the gap.
    # Should be dropped.

    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   12  .  G   C   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_gap_data)

    with closing(pysam.VariantFile(
            str(out_vcf.with_suffix(".vcf")))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 0


def test_vcf_liftover_outside_chain(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    # Chain covers chrA:0-20.
    # Variant at chrA:22 is outside.
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   22  .  G   C   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_data)

    with closing(pysam.VariantFile(
            str(out_vcf.with_suffix(".vcf")))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 0


def test_chain_loading(
    liftover_data: GenomicResourceRepo,
) -> None:
    res = liftover_data.get_resource("liftover_chain")
    chain = build_liftover_chain_from_resource(res).open()

    # Identity: chrA:0-10 -> chrB:0-10 (+)
    # chrA:5 (0-based 4) -> chrB:5 (0-based 4)
    lo = chain.convert_coordinate("chrA", 5)
    assert lo is not None
    chrom, pos, strand, _ = lo
    assert chrom == "chrB"
    assert pos == 5
    assert strand == "+"


def test_vcf_liftover_simple(
    tmp_path: pathlib.Path,
    liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
##contig=<ID=bar>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
foo    5   .  A   C   .    .      .    GT     0/0  0/0  0/1
foo    6   .  C   T   .    .      .    GT     0/1  0/0  0/0
foo    7   .  G   A   .    .      .    GT     0/0  1/0  0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_grr_fixture)

    assert out_vcf.with_suffix(".vcf").exists()

    with closing(pysam.VariantFile(
            str(out_vcf.with_suffix(".vcf")))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 3


@pytest.fixture
def dae_transmitted_data(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    """Create pedigree and DAE transmitted variant files for testing."""
    # Setup pedigree file
    pedigree_file = setup_pedigree(
        tmp_path / "pedigree.ped",
        textwrap.dedent("""
            familyId personId dadId momId sex status role
            f1       mom1     0     0     2   1      mom
            f1       dad1     0     0     1   1      dad
            f1       ch1      dad1  mom1  1   2      prb
        """),
    )

    # Setup DAE transmitted variant files
    # Variant at chrA:6 A->C should map to chrB:6 A->C (identity region)
    summary_file, toomany_file = setup_dae_transmitted(
        tmp_path,
        textwrap.dedent("""
            chr  position variant   familyData all.nParCalled \
all.prcntParCalled all.nAltAlls all.altFreq
            chrA 6        sub(A->C) \
f1:0100/2221:0||0||0||0/0||0||0||0/0||0||0||0 2 100.00 1 50.00
        """),
        textwrap.dedent("""
            chr position variant familyData
        """),
    )

    return pedigree_file, summary_file, toomany_file


def test_dae_liftover_simple(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    dae_transmitted_data: tuple[pathlib.Path, pathlib.Path, pathlib.Path],
) -> None:
    """Test basic dae_liftover functionality."""
    pedigree_file, summary_file, _toomany_file = dae_transmitted_data

    out_prefix = tmp_path / "lifted"
    argv = [
        str(pedigree_file),
        str(summary_file),
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_prefix),
    ]

    dae_liftover_main(argv, grr=liftover_data)

    # Check that output files were created
    assert out_prefix.with_suffix(".txt").exists()
    assert out_prefix.with_name(f"{out_prefix.name}-TOOMANY.txt").exists()

    # Verify the output contains the lifted variant
    with open(out_prefix.with_suffix(".txt"), encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 1  # Header + at least one variant
        # Check that chrB is in the output (lifted from chrA)
        content = "".join(lines)
        assert "chrB" in content
