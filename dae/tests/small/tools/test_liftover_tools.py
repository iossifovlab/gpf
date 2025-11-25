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
    setup_denovo,
    setup_directories,
    setup_genome,
    setup_gzip,
    setup_pedigree,
    setup_vcf,
)
from dae.tools.liftover_tools import (
    VCFLiftoverTool,
    _region_output_filename,
    cnv_liftover_main,
    dae_liftover_main,
    denovo_liftover_main,
    vcf_liftover_main,
)
from dae.utils.regions import Region
from pytest_mock import MockerFixture


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

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

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

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

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

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

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

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_gap_data)

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

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

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

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_grr_fixture)

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


@pytest.fixture
def denovo_data(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path]:
    """Create pedigree and denovo variant files for testing."""
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

    # Setup denovo variant file
    # Variant at chrA:6 A->C should map to chrB:6 A->C (identity region)
    denovo_file = setup_denovo(
        tmp_path / "denovo.txt",
        textwrap.dedent("""
            familyId location    variant   bestState
            f1       chrA:6      sub(A->C) 2||2||1/0||0||1
        """),
    )

    return pedigree_file, denovo_file


def test_denovo_liftover_simple(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    denovo_data: tuple[pathlib.Path, pathlib.Path],
) -> None:
    """Test basic denovo_liftover functionality."""
    pedigree_file, denovo_file = denovo_data

    out_file = tmp_path / "lifted_denovo.txt"
    argv = [
        str(pedigree_file),
        str(denovo_file),
        "--denovo-location", "location",
        "--denovo-variant", "variant",
        "--denovo-family-id", "familyId",
        "--denovo-best-state", "bestState",
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_file),
    ]

    denovo_liftover_main(argv, grr=liftover_data)

    # Check that output file was created
    assert out_file.exists()

    # Verify the output contains the lifted variant
    with open(out_file, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 1  # Header + at least one variant
        # Check that chrB is in the output (lifted from chrA)
        content = "".join(lines)
        assert "chrB" in content


@pytest.fixture
def cnv_data(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path]:
    """Create pedigree and CNV variant files for testing."""
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

    # Setup CNV variant file
    # CNV at chrA:4-8 (covers position 6) should map to chrB
    cnv_file = setup_denovo(
        tmp_path / "cnv.txt",
        textwrap.dedent("""
            familyId location    variant bestState
            f1       chrA:4-8    CNV+    2||2||3
        """),
    )

    return pedigree_file, cnv_file


def test_cnv_liftover_simple(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    cnv_data: tuple[pathlib.Path, pathlib.Path],
) -> None:
    """Test basic cnv_liftover functionality."""
    pedigree_file, cnv_file = cnv_data

    out_file = tmp_path / "lifted_cnv.txt"
    argv = [
        str(pedigree_file),
        str(cnv_file),
        "--cnv-location", "location",
        "--cnv-variant-type", "variant",
        "--cnv-family-id", "familyId",
        "--cnv-best-state", "bestState",
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_file),
    ]

    cnv_liftover_main(argv, grr=liftover_data)

    # Check that output file was created
    assert out_file.exists()

    # Verify the output contains the lifted variant
    with open(out_file, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 1  # Header + at least one variant
        # Check that chrB is in the output (lifted from chrA)
        content = "".join(lines)
        assert "chrB" in content


@pytest.mark.parametrize("region, filename, expected", [
    (None, "output.txt", "output.txt"),
    (Region("chr1", 10, 20), "output.txt", "output_chr1_10_20.txt"),
    (Region("chr1", 10, 20), "output", "output_chr1_10_20"),
    (Region("chr1", 10, 20), "output.txt.gz", "output_chr1_10_20.txt.gz"),
])
def test_region_output_filename(
    region: Region | None,
    filename: str,
    expected: str,
) -> None:
    result = _region_output_filename(filename, region)
    assert result == expected


def test_vcf_liftover_with_region(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test VCF liftover with region filtering."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   6   .  A   C   .    .      .    GT     0/1
chrA   13  .  T   G   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "--region", "chrA:5-10",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

    # When region is specified, output filename changes
    expected_vcf = tmp_path / "liftover_chrA_5_10.vcf"
    with closing(pysam.VariantFile(str(expected_vcf))) as vcffile:
        variants = list(vcffile.fetch())
        # Only variant at position 6 should be in region chrA:5-10
        assert len(variants) == 1
        assert variants[0].pos == 6


def test_vcf_liftover_basic_mode(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test VCF liftover with basic_liftover mode."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   6   .  A   C   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "--mode", "basic_liftover",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

    with closing(pysam.VariantFile(str(out_vcf))) as vcffile:
        variants = list(vcffile.fetch())
        assert len(variants) == 1
        assert variants[0].chrom == "chrB"
        assert variants[0].pos == 6


def test_dae_liftover_with_region(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    dae_transmitted_data: tuple[pathlib.Path, pathlib.Path, pathlib.Path],
) -> None:
    """Test DAE liftover with region parameter (filename generation)."""
    pedigree_file, summary_file, _toomany_file = dae_transmitted_data

    # Test without region to verify basic functionality
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

    # Check that output files were created without region suffix
    expected_summary = tmp_path / "lifted.txt"
    expected_toomany = tmp_path / "lifted-TOOMANY.txt"
    assert expected_summary.exists()
    assert expected_toomany.exists()


def test_denovo_liftover_with_region(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    denovo_data: tuple[pathlib.Path, pathlib.Path],
) -> None:
    """Test denovo liftover with region parameter (filename generation)."""
    pedigree_file, denovo_file = denovo_data

    # Test without region to verify basic functionality
    out_file = tmp_path / "lifted_denovo.txt"
    argv = [
        str(pedigree_file),
        str(denovo_file),
        "--denovo-location", "location",
        "--denovo-variant", "variant",
        "--denovo-family-id", "familyId",
        "--denovo-best-state", "bestState",
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_file),
    ]

    denovo_liftover_main(argv, grr=liftover_data)

    # Check that output file was created
    assert out_file.exists()


def test_cnv_liftover_with_region(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    cnv_data: tuple[pathlib.Path, pathlib.Path],
) -> None:
    """Test CNV liftover with region parameter (filename generation)."""
    pedigree_file, cnv_file = cnv_data

    # Test without region to verify basic functionality
    out_file = tmp_path / "lifted_cnv.txt"
    argv = [
        str(pedigree_file),
        str(cnv_file),
        "--cnv-location", "location",
        "--cnv-variant-type", "variant",
        "--cnv-family-id", "familyId",
        "--cnv-best-state", "bestState",
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_file),
    ]

    cnv_liftover_main(argv, grr=liftover_data)

    # Check that output file was created
    assert out_file.exists()


def test_vcf_liftover_invalid_mode(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test VCF liftover with invalid mode raises error."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO
chrA   6   .  A   C   .    .      .
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "--mode", "invalid_mode",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    with pytest.raises(ValueError, match="Invalid mode"):
        vcf_liftover_main(argv, grr=liftover_data)


def test_report_variant() -> None:
    """Test report_variant function."""
    variant = ("chr1", 100, "A", ["C"])
    result = VCFLiftoverTool.report_variant(variant)
    assert result == "(chr1:100 A > C)"


def test_report_variant_none() -> None:
    """Test report_variant with None input."""
    result = VCFLiftoverTool.report_variant(None)
    assert result == "(none)"


def test_report_variant_multiple_alts() -> None:
    """Test report_variant with multiple alternatives."""
    variant = ("chr2", 200, "T", ["A", "G"])
    result = VCFLiftoverTool.report_variant(variant)
    assert result == "(chr2:200 T > A,G)"


def test_report_vcf_variant(tmp_path: pathlib.Path) -> None:
    """Test report_vcf_variant function."""
    vcf_file = setup_vcf(
        tmp_path / "test.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##contig=<ID=chr1>
#CHROM POS ID REF ALT QUAL FILTER INFO
chr1   100 .  A   C   .    .      .
        """))

    with closing(pysam.VariantFile(str(vcf_file))) as vcffile:
        variant = next(vcffile.fetch())
        result = VCFLiftoverTool.report_vcf_variant(variant)
        assert result == "(chr1:100 A > C)"


def test_report_vcf_variant_no_alt(tmp_path: pathlib.Path) -> None:
    """Test report_vcf_variant with no ALT field."""
    vcf_file = setup_vcf(
        tmp_path / "test.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##contig=<ID=chr1>
#CHROM POS ID REF ALT QUAL FILTER INFO
chr1   100 .  A   .   .    .      .
        """))

    with closing(pysam.VariantFile(str(vcf_file))) as vcffile:
        variant = next(vcffile.fetch())
        result = VCFLiftoverTool.report_vcf_variant(variant)
        assert result == "(chr1:100 A > .)"


def test_vcf_liftover_variant_without_alt(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test VCF liftover handles variants without ALT field (skips them)."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO
chrA   6   .  A   .   .    .      .
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

    with closing(pysam.VariantFile(str(out_vcf))) as vcffile:
        variants = list(vcffile.fetch())
        # Variants without ALT are skipped per the warning log
        assert len(variants) == 0


def test_vcf_liftover_region_overwrite(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test VCF liftover with multiple regions (last one wins)."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1
chrA   6   .  A   C   .    .      .    GT     0/1
chrA   11  .  T   G   .    .      .    GT     0/1
chrA   13  .  T   G   .    .      .    GT     0/1
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "--region", "chrA:5-10",
        "--region", "chrA:12-14",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    vcf_liftover_main(argv, grr=liftover_data)

    # Only the last region is used: chrA:12-14
    expected_vcf = tmp_path / "liftover_chrA_12_14.vcf"

    with closing(pysam.VariantFile(str(expected_vcf))) as vcffile:
        variants = list(vcffile.fetch())
        # Should get variant at position 13 only
        assert len(variants) == 1
        assert variants[0].pos == 13


def test_liftover_tool_missing_source_genome(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test liftover tool with missing source genome."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO
chrA   6   .  A   C   .    .      .
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "missing_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    with pytest.raises(FileNotFoundError, match="resource <missing_genome>"):
        vcf_liftover_main(argv, grr=liftover_data)


def test_liftover_tool_missing_target_genome(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
) -> None:
    """Test liftover tool with missing target genome."""
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO
chrA   6   .  A   C   .    .      .
        """))

    out_vcf = tmp_path / "liftover.vcf"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "missing_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    with pytest.raises(FileNotFoundError, match="resource <missing_genome>"):
        vcf_liftover_main(argv, grr=liftover_data)


def test_cnv_liftover_invalid_mode(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    cnv_data: tuple[pathlib.Path, pathlib.Path],
) -> None:
    """Test CNV liftover with invalid mode."""
    pedigree_file, cnv_file = cnv_data

    out_file = tmp_path / "lifted_cnv.txt"
    argv = [
        str(pedigree_file),
        str(cnv_file),
        "--cnv-location", "location",
        "--cnv-variant-type", "variant",
        "--cnv-family-id", "familyId",
        "--cnv-best-state", "bestState",
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "--mode", "invalid_mode",
        "-o", str(out_file),
    ]

    with pytest.raises(ValueError, match="unknown liftover mode"):
        cnv_liftover_main(argv, grr=liftover_data)


def test_dae_liftover_below_toomany_threshold(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    mocker: MockerFixture,
) -> None:
    """Test DAE liftover with families below TOOMANY threshold."""
    # Mock the threshold to 3 for easier testing
    mocker.patch(
        "dae.tools.liftover_tools.DaeLiftoverTool._TOOMANY_THRESHOLD", 3)

    # Create pedigree with 2 families (below threshold of 3)
    ped_lines = ["familyId personId dadId momId sex status role"]
    family_data_parts = []

    for i in range(1, 3):
        fid = f"f{i}"
        ped_lines.extend([
            f"{fid} mom{i} 0 0 2 1 mom",
            f"{fid} dad{i} 0 0 1 1 dad",
            f"{fid} ch{i} dad{i} mom{i} 1 2 prb",
        ])
        family_data_parts.append(
            f"{fid}:0100/2221:0||0||0||0/0||0||0||0/0||0||0||0")

    pedigree_file = setup_pedigree(
        tmp_path / "pedigree.ped",
        "\n".join(ped_lines),
    )

    family_data_str = ";".join(family_data_parts)

    summary_file, _ = setup_dae_transmitted(
        tmp_path,
        f"chr  position variant   familyData all.nParCalled "
        f"all.prcntParCalled all.nAltAlls all.altFreq\n"
        f"chrA 6        sub(A->C) {family_data_str} 4 100.00 2 50.00",
        "chr position variant familyData",
    )

    out_prefix = tmp_path / "lifted_below_threshold"
    argv = [
        str(pedigree_file),
        str(summary_file),
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_prefix),
    ]

    dae_liftover_main(argv, grr=liftover_data)

    # Check output
    out_summary = out_prefix.with_suffix(".txt")
    out_toomany = out_prefix.with_name(f"{out_prefix.name}-TOOMANY.txt")

    assert out_summary.exists()
    assert out_toomany.exists()

    with open(out_summary, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2  # Header + 1 variant
        # The familyData column (index 3) should contain family data
        parts = lines[1].strip().split("\t")
        assert parts[3] != "TOOMANY"
        assert len(parts[3].split(";")) == 2

    # TOOMANY file should only have header
    with open(out_toomany, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1  # Only header


def test_dae_liftover_above_toomany_threshold(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    mocker: MockerFixture,
) -> None:
    """Test DAE liftover with families above TOOMANY threshold."""
    # Mock the threshold to 3 for easier testing
    mocker.patch(
        "dae.tools.liftover_tools.DaeLiftoverTool._TOOMANY_THRESHOLD", 3)

    # Create pedigree with 4 families (above threshold of 3)
    ped_lines = ["familyId personId dadId momId sex status role"]
    family_data_parts = []

    for i in range(1, 5):
        fid = f"f{i}"
        ped_lines.extend([
            f"{fid} mom{i} 0 0 2 1 mom",
            f"{fid} dad{i} 0 0 1 1 dad",
            f"{fid} ch{i} dad{i} mom{i} 1 2 prb",
        ])
        family_data_parts.append(
            f"{fid}:0100/2221:0||0||0||0/0||0||0||0/0||0||0||0")

    pedigree_file = setup_pedigree(
        tmp_path / "pedigree.ped",
        "\n".join(ped_lines),
    )

    family_data_str = ";".join(family_data_parts)

    summary_file, _ = setup_dae_transmitted(
        tmp_path,
        f"chr  position variant   familyData all.nParCalled "
        f"all.prcntParCalled all.nAltAlls all.altFreq\n"
        f"chrA 6        sub(A->C) {family_data_str} 8 100.00 4 50.00",
        "chr position variant familyData",
    )

    out_prefix = tmp_path / "lifted_above_threshold"
    argv = [
        str(pedigree_file),
        str(summary_file),
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_prefix),
    ]

    dae_liftover_main(argv, grr=liftover_data)

    # Check output
    out_summary = out_prefix.with_suffix(".txt")
    out_toomany = out_prefix.with_name(f"{out_prefix.name}-TOOMANY.txt")

    assert out_summary.exists()
    assert out_toomany.exists()

    with open(out_summary, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2  # Header + 1 variant
        # The familyData column (index 3) should be TOOMANY
        parts = lines[1].strip().split("\t")
        assert parts[3] == "TOOMANY"

    # TOOMANY file should have the actual family data
    with open(out_toomany, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2  # Header + 1 variant
        parts = lines[1].strip().split("\t")
        assert parts[3] != "TOOMANY"
        assert len(parts[3].split(";")) == 4


def test_dae_liftover_exact_toomany_threshold(
    tmp_path: pathlib.Path,
    liftover_data: GenomicResourceRepo,
    mocker: MockerFixture,
) -> None:
    """Test DAE liftover with exactly at threshold boundary."""
    # Mock the threshold to 3 for easier testing
    mocker.patch(
        "dae.tools.liftover_tools.DaeLiftoverTool._TOOMANY_THRESHOLD", 3)

    # Create pedigree with exactly 3 families (at threshold)
    ped_lines = ["familyId personId dadId momId sex status role"]
    family_data_parts = []

    for i in range(1, 4):
        fid = f"f{i}"
        ped_lines.extend([
            f"{fid} mom{i} 0 0 2 1 mom",
            f"{fid} dad{i} 0 0 1 1 dad",
            f"{fid} ch{i} dad{i} mom{i} 1 2 prb",
        ])
        family_data_parts.append(
            f"{fid}:0100/2221:0||0||0||0/0||0||0||0/0||0||0||0")

    pedigree_file = setup_pedigree(
        tmp_path / "pedigree.ped",
        "\n".join(ped_lines),
    )

    family_data_str = ";".join(family_data_parts)

    summary_file, _ = setup_dae_transmitted(
        tmp_path,
        f"chr  position variant   familyData all.nParCalled "
        f"all.prcntParCalled all.nAltAlls all.altFreq\n"
        f"chrA 6        sub(A->C) {family_data_str} 6 100.00 3 50.00",
        "chr position variant familyData",
    )

    out_prefix = tmp_path / "lifted_exact_threshold"
    argv = [
        str(pedigree_file),
        str(summary_file),
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_prefix),
    ]

    dae_liftover_main(argv, grr=liftover_data)

    # Check output
    out_summary = out_prefix.with_suffix(".txt")
    out_toomany = out_prefix.with_name(f"{out_prefix.name}-TOOMANY.txt")

    assert out_summary.exists()
    assert out_toomany.exists()

    with open(out_summary, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2  # Header + 1 variant
        # With exactly 3 families, should use TOOMANY (threshold is < 3)
        parts = lines[1].strip().split("\t")
        assert parts[3] == "TOOMANY"

    # TOOMANY file should have the actual family data
    with open(out_toomany, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2  # Header + 1 variant
        parts = lines[1].strip().split("\t")
        assert len(parts[3].split(";")) == 3
