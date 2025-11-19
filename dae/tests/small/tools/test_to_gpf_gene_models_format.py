# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gzip
import pathlib

import pytest
from dae.genomic_resources.gene_models.gene_models_factory import (
    build_gene_models_from_file,
)
from dae.genomic_resources.testing import convert_to_tab_separated
from dae.tools.to_gpf_gene_models_format import main

REFFLAT_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx2  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
BRCA1     tx4  1     -      200     300   210      290    2         200,250    220,300
"""  # noqa

# GTF format content
GTF_CONTENT = """
1	test	transcript	10	100	.	+	.	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
1	test	exon	10	15	.	+	.	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
1	test	exon	50	60	.	+	.	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
1	test	exon	70	100	.	+	.	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
1	test	CDS	12	15	.	+	0	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
1	test	CDS	50	60	.	+	0	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
1	test	CDS	70	95	.	+	2	gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";
"""  # noqa


@pytest.fixture
def refflat_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a test refflat gene models file."""
    input_file = tmp_path / "input_genes.txt"
    input_file.write_text(convert_to_tab_separated(REFFLAT_CONTENT))
    return input_file


@pytest.fixture
def gtf_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a test GTF gene models file."""
    input_file = tmp_path / "input_genes.gtf"
    input_file.write_text(GTF_CONTENT.strip())
    return input_file


@pytest.fixture
def gene_mapping_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a gene name mapping file."""
    mapping_file = tmp_path / "gene_mapping.txt"
    mapping_file.write_text(convert_to_tab_separated("""
        from   to
        POGZ   gosho
        TP53   pesho
        BRCA1  brca_mapped
    """))
    return mapping_file


@pytest.fixture
def chrom_mapping_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a chromosome name mapping file."""
    mapping_file = tmp_path / "chrom_mapping.txt"
    mapping_file.write_text("1\tchr1\n17\tchr17\n")
    return mapping_file


def test_to_gpf_gene_models_format_basic(
    refflat_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test basic conversion without optional arguments."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert gene models
    main([
        str(refflat_file),
        str(output_file),
    ])

    # Then: Output file should be created and gzipped by default
    assert output_file.with_suffix(".txt.gz").exists()

    # Verify the converted gene models can be loaded
    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    assert set(gene_models.gene_names()) == {"TP53", "POGZ", "BRCA1"}
    assert len(gene_models.transcript_models) == 4


def test_to_gpf_gene_models_format_with_explicit_format(
    gtf_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test conversion with explicit format specification."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert GTF with explicit format
    main([
        str(gtf_file),
        str(output_file),
        "--gm-format", "gtf",
    ])

    # Then: Output should be created
    assert output_file.with_suffix(".txt.gz").exists()

    # Verify the converted gene models
    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    assert "TP53" in gene_models.gene_names()
    assert len(gene_models.transcript_models) == 1


def test_to_gpf_gene_models_format_with_gene_mapping(
    refflat_file: pathlib.Path,
    gene_mapping_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test conversion with gene name mapping."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert with gene mapping
    main([
        str(refflat_file),
        str(output_file),
        "--gm-names", str(gene_mapping_file),
    ])

    # Then: Gene names should be mapped
    assert output_file.with_suffix(".txt.gz").exists()

    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    # Check that gene names are mapped
    assert set(gene_models.gene_names()) == {"pesho", "gosho", "brca_mapped"}
    assert "TP53" not in gene_models.gene_names()
    assert "POGZ" not in gene_models.gene_names()
    assert "BRCA1" not in gene_models.gene_names()


def test_to_gpf_gene_models_format_with_chrom_mapping(
    refflat_file: pathlib.Path,
    chrom_mapping_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test conversion with chromosome name mapping."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert with chromosome mapping
    main([
        str(refflat_file),
        str(output_file),
        "--chrom-mapping", str(chrom_mapping_file),
    ])

    # Then: Chromosome names should be mapped
    assert output_file.with_suffix(".txt.gz").exists()

    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    # Check that chromosomes are mapped
    assert gene_models.has_chromosome("chr1")
    assert gene_models.has_chromosome("chr17")
    assert not gene_models.has_chromosome("1")
    assert not gene_models.has_chromosome("17")

    # Verify transcripts have mapped chromosomes
    for tm in gene_models.transcript_models.values():
        assert tm.chrom.startswith("chr")


def test_to_gpf_gene_models_format_with_all_options(
    refflat_file: pathlib.Path,
    gene_mapping_file: pathlib.Path,
    chrom_mapping_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test conversion with all optional arguments."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert with all options
    main([
        str(refflat_file),
        str(output_file),
        "--gm-format", "refflat",
        "--gm-names", str(gene_mapping_file),
        "--chrom-mapping", str(chrom_mapping_file),
    ])

    # Then: Both gene and chromosome names should be mapped
    assert output_file.with_suffix(".txt.gz").exists()

    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    # Check gene name mapping
    assert set(gene_models.gene_names()) == {"pesho", "gosho", "brca_mapped"}

    # Check chromosome mapping
    assert gene_models.has_chromosome("chr1")
    assert gene_models.has_chromosome("chr17")

    # Verify both mappings are applied to transcripts
    for tm in gene_models.transcript_models.values():
        assert tm.chrom.startswith("chr")
        assert tm.gene in {"pesho", "gosho", "brca_mapped"}


def test_to_gpf_gene_models_format_output_is_gzipped(
    refflat_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test that output is gzipped by default."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert gene models
    main([
        str(refflat_file),
        str(output_file),
    ])

    # Then: Output should be gzipped
    gzipped_file = output_file.with_suffix(".txt.gz")
    assert gzipped_file.exists()

    # Verify it's actually gzipped
    with gzip.open(gzipped_file, "rt") as f:
        content = f.read()
        assert len(content) > 0
        # Check for default format header
        assert "#chr" in content or "chr" in content.lower()


def test_to_gpf_gene_models_format_output_content_format(
    refflat_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test that output is in the default GPF gene models format."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert gene models
    main([
        str(refflat_file),
        str(output_file),
    ])

    # Then: Check output format structure
    gzipped_file = output_file.with_suffix(".txt.gz")
    with gzip.open(gzipped_file, "rt") as f:
        lines = f.readlines()

    # Should have header line
    assert len(lines) > 0
    header = lines[0].strip()

    # Header should contain expected columns for default format
    assert "#chr" in header or "chr" in header

    # Should have data lines (one per transcript)
    assert len(lines) > 1


def test_to_gpf_gene_models_format_preserves_transcript_details(
    refflat_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test that transcript details are preserved in conversion."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert gene models
    main([
        str(refflat_file),
        str(output_file),
    ])

    # Then: Load and verify transcript details
    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    # Check specific transcript details
    tp53_transcripts = gene_models.gene_models_by_gene_name("TP53")
    assert tp53_transcripts is not None
    assert len(tp53_transcripts) == 2

    # Verify transcript properties are preserved
    for tm in tp53_transcripts:
        assert tm.chrom == "1"
        assert tm.strand == "+"
        # Note: coordinates may be adjusted during conversion
        # (refflat is 0-based, default format is 1-based)
        assert tm.tx[0] > 0
        assert tm.tx[1] == 100
        assert tm.cds[0] > 0
        assert tm.cds[1] == 95


def test_to_gpf_gene_models_format_with_format_refflat(
    refflat_file: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test conversion with explicit refflat format."""
    output_file = tmp_path / "output_genes.txt"

    # When: Convert with explicit refflat format
    main([
        str(refflat_file),
        str(output_file),
        "--gm-format", "refflat",
    ])

    # Then: Should succeed
    assert output_file.with_suffix(".txt.gz").exists()

    gene_models = build_gene_models_from_file(
        str(output_file.with_suffix(".txt.gz")))
    gene_models.load()

    assert len(gene_models.transcript_models) == 4
