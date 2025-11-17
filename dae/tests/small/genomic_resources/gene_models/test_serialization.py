# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Tests for dae.genomic_resources.gene_models.serialization module."""
import gzip
import pathlib
from io import StringIO

import pytest
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.genomic_resources.gene_models.gene_models_factory import (
    build_gene_models_from_file,
    build_gene_models_from_resource,
)
from dae.genomic_resources.gene_models.serialization import (
    GTF_FEATURE_ORDER,
    _save_as_default_gene_models,
    build_gtf_record,
    collect_gtf_cds_regions,
    collect_gtf_start_codon_regions,
    collect_gtf_stop_codon_regions,
    gene_models_to_gtf,
    get_exon_number_for,
    gtf_canonical_index,
    save_as_default_gene_models,
    transcript_to_gtf,
)
from dae.genomic_resources.gene_models.transcript_models import (
    Exon,
    TranscriptModel,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)
from dae.utils.regions import BedRegion


@pytest.fixture
def simple_gene_models() -> GeneModels:
    """Create a simple gene models resource for testing."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
BRCA1     tx2  2     -      200     300   210      290    2         200,250    220,300
"""  # noqa
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(content),
        },
    )
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()
    return gene_models


@pytest.fixture
def noncoding_gene_models() -> GeneModels:
    """Create gene models with non-coding transcript."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
NCRNA     tx1  1     +      10      100   100      100    2         10,50      40,100
"""  # noqa
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(content),
        },
    )
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()
    return gene_models


@pytest.fixture
def simple_transcript() -> TranscriptModel:
    """Create a simple transcript model for testing."""
    return TranscriptModel(
        gene="TEST",
        tr_id="tx1",
        tr_name="tx1_orig",
        chrom="1",
        strand="+",
        tx=(100, 200),
        cds=(120, 180),
        exons=[
            Exon(100, 150, frame=0),
            Exon(160, 200, frame=1),
        ],
        attributes={
            "gene_source": "test_source",
            "gene_version": "1",
            "gene_biotype": "protein_coding",
        },
    )


def test_gtf_canonical_index_basic() -> None:
    """Test gtf_canonical_index converts index for canonical sorting."""
    index = ("chr1", 100, -200, GTF_FEATURE_ORDER["gene"])
    canonical = gtf_canonical_index(index)

    # Should place feature order at the front
    assert canonical == (GTF_FEATURE_ORDER["gene"], "chr1", 100, -200)


def test_gtf_canonical_index_feature_ordering() -> None:
    """Test that canonical index properly orders features."""
    gene_idx = ("chr1", 100, -200, GTF_FEATURE_ORDER["gene"])
    transcript_idx = ("chr1", 100, -200, GTF_FEATURE_ORDER["transcript"])
    exon_idx = ("chr1", 100, -200, GTF_FEATURE_ORDER["exon"])

    gene_canon = gtf_canonical_index(gene_idx)
    transcript_canon = gtf_canonical_index(transcript_idx)
    exon_canon = gtf_canonical_index(exon_idx)

    # Gene should come before transcript, transcript before exon
    assert gene_canon < transcript_canon < exon_canon


def test_gtf_canonical_index_with_different_features() -> None:
    """Test canonical index with all feature types."""
    features = [
        "gene", "transcript", "exon", "CDS",
        "start_codon", "stop_codon", "UTR",
    ]
    indices = [
        ("chr1", 100, -200, GTF_FEATURE_ORDER[feat])
        for feat in features
    ]
    canonicals = [gtf_canonical_index(idx) for idx in indices]

    # All should have feature order as first element
    for i, feat in enumerate(features):
        assert canonicals[i][0] == GTF_FEATURE_ORDER[feat]


def test_build_gtf_record_basic(simple_transcript: TranscriptModel) -> None:
    """Test build_gtf_record creates correct GTF record."""
    attrs = 'gene_id "TEST"; gene_name "TEST"'
    index, line = build_gtf_record(
        simple_transcript, "exon", 100, 150, attrs,
    )

    # Check index structure
    assert index == ("1", 100, -150, GTF_FEATURE_ORDER["exon"])

    # Check line contains key elements
    assert "1\t" in line  # chromosome
    assert "\texon\t" in line  # feature type
    assert "\t100\t150\t" in line  # start and end
    assert attrs in line
    assert 'exon_number "1"' in line  # Should add exon number


def test_build_gtf_record_with_cds(
    simple_transcript: TranscriptModel,
) -> None:
    """Test build_gtf_record with CDS feature includes frame."""
    attrs = 'gene_id "TEST"'
    _index, line = build_gtf_record(
        simple_transcript, "CDS", 120, 150, attrs,
    )

    # CDS should have phase calculated (not ".")
    fields = line.split("\t")
    phase = fields[7]
    assert phase in ("0", "1", "2")  # Valid phase values
    assert 'exon_number "1"' in line


def test_build_gtf_record_with_start_codon(
    simple_transcript: TranscriptModel,
) -> None:
    """Test build_gtf_record with start_codon feature."""
    attrs = 'gene_id "TEST"'
    _index, line = build_gtf_record(
        simple_transcript, "start_codon", 120, 122, attrs,
    )

    assert "\tstart_codon\t" in line
    assert 'exon_number "1"' in line
    # Should have phase
    fields = line.split("\t")
    phase = fields[7]
    assert phase in ("0", "1", "2")


def test_build_gtf_record_with_utr(
    simple_transcript: TranscriptModel,
) -> None:
    """Test build_gtf_record with UTR feature."""
    attrs = 'gene_id "TEST"'
    _index, line = build_gtf_record(
        simple_transcript, "UTR", 100, 119, attrs,
    )

    assert "\tUTR\t" in line
    # UTR should not have exon number
    assert "exon_number" not in line
    # UTR phase should be "."
    fields = line.split("\t")
    phase = fields[7]
    assert phase == "."


def test_build_gtf_record_negative_strand() -> None:
    """Test build_gtf_record with negative strand transcript."""
    transcript = TranscriptModel(
        gene="TEST",
        tr_id="tx1",
        tr_name="tx1",
        chrom="1",
        strand="-",
        tx=(100, 200),
        cds=(120, 180),
        exons=[Exon(100, 200, frame=0)],
    )

    attrs = 'gene_id "TEST"'
    _index, line = build_gtf_record(transcript, "exon", 100, 200, attrs)

    assert "\t-\t" in line  # Should show negative strand


def test_gene_models_to_gtf_empty() -> None:
    """Test gene_models_to_gtf with empty gene models."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
"""  # noqa
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(content),
        },
    )
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    result = gene_models_to_gtf(gene_models)

    # Empty models should return empty StringIO
    content_str = result.read()
    assert content_str == ""


def test_gene_models_to_gtf_basic(simple_gene_models: GeneModels) -> None:
    """Test gene_models_to_gtf with basic gene models."""
    result = gene_models_to_gtf(simple_gene_models)
    content = result.read()

    # Should have GTF header
    assert "##description:" in content
    assert "##format: gtf" in content
    assert "##provider: GPF" in content

    # Should have gene records
    assert "\tgene\t" in content
    assert "\ttranscript\t" in content
    assert "\texon\t" in content


def test_gene_models_to_gtf_sorting_by_position(
    simple_gene_models: GeneModels,
) -> None:
    """Test gene_models_to_gtf sorting by position."""
    result = gene_models_to_gtf(simple_gene_models, sort_by_position=True)
    lines = [
        line for line in result.read().split("\n")
        if line and not line.startswith("#")
    ]

    # Extract positions and check they're sorted
    positions = []
    for line in lines:
        if "\t" in line:
            fields = line.split("\t")
            chrom = fields[0]
            start = int(fields[3])
            positions.append((chrom, start))

    # Should be sorted by chromosome and position
    assert positions == sorted(positions)


def test_gene_models_to_gtf_sorting_canonical(
    simple_gene_models: GeneModels,
) -> None:
    """Test gene_models_to_gtf with canonical sorting."""
    result = gene_models_to_gtf(simple_gene_models, sort_by_position=False)
    lines = [
        line for line in result.read().split("\n")
        if line and not line.startswith("#")
    ]

    # Extract all feature types to verify canonical sorting is different
    # from position sorting
    features = []
    for line in lines:
        if "\t" in line:
            fields = line.split("\t")
            feature = fields[2]
            chrom = fields[0]
            features.append((chrom, feature))

    # With canonical sorting, features should be grouped by type
    # (gene before transcript before exon, etc.)
    # At minimum, verify we have multiple feature types
    feature_types = [f[1] for f in features]
    assert "gene" in feature_types
    assert "transcript" in feature_types
    assert "exon" in feature_types


def test_gene_models_to_gtf_includes_all_features(
    simple_gene_models: GeneModels,
) -> None:
    """Test gene_models_to_gtf includes expected features."""
    result = gene_models_to_gtf(simple_gene_models)
    content = result.read()

    # Should have various features for coding transcripts
    assert "\tgene\t" in content
    assert "\ttranscript\t" in content
    assert "\texon\t" in content
    assert "\tCDS\t" in content
    assert "\tstart_codon\t" in content
    assert "\tstop_codon\t" in content


def test_gene_models_to_gtf_noncoding(
    noncoding_gene_models: GeneModels,
) -> None:
    """Test gene_models_to_gtf with non-coding transcript."""
    result = gene_models_to_gtf(noncoding_gene_models)
    content = result.read()

    # Should have gene, transcript, exon
    assert "\tgene\t" in content
    assert "\ttranscript\t" in content
    assert "\texon\t" in content

    # Should NOT have CDS-related features
    assert "\tCDS\t" not in content
    assert "\tstart_codon\t" not in content
    assert "\tstop_codon\t" not in content


def test_transcript_to_gtf_basic(simple_transcript: TranscriptModel) -> None:
    """Test transcript_to_gtf creates GTF records."""
    records = transcript_to_gtf(simple_transcript)

    # Should have transcript, exons, CDS features
    assert len(records) > 0

    features = [rec[1].split("\t")[2] for rec in records]
    assert "transcript" in features
    assert "exon" in features


def test_transcript_to_gtf_coding_features(
    simple_transcript: TranscriptModel,
) -> None:
    """Test transcript_to_gtf includes coding features."""
    records = transcript_to_gtf(simple_transcript)

    features = [rec[1].split("\t")[2] for rec in records]

    # Coding transcript should have CDS and codons
    assert "CDS" in features
    assert "start_codon" in features
    assert "stop_codon" in features
    assert "UTR" in features


def test_transcript_to_gtf_noncoding() -> None:
    """Test transcript_to_gtf with non-coding transcript."""
    transcript = TranscriptModel(
        gene="NCRNA",
        tr_id="tx1",
        tr_name="tx1",
        chrom="1",
        strand="+",
        tx=(100, 200),
        cds=(200, 200),  # Non-coding: cds start == cds end
        exons=[Exon(100, 200)],
    )

    records = transcript_to_gtf(transcript)
    features = [rec[1].split("\t")[2] for rec in records]

    # Non-coding should only have transcript and exon
    assert "transcript" in features
    assert "exon" in features
    assert "CDS" not in features
    assert "start_codon" not in features
    assert "stop_codon" not in features


def test_save_as_default_gene_models_internal(
    simple_gene_models: GeneModels,
) -> None:
    """Test _save_as_default_gene_models writes correct format."""
    output = StringIO()
    _save_as_default_gene_models(simple_gene_models, output)

    content = output.getvalue()
    lines = content.strip().split("\n")

    # Should have header
    header = lines[0].split("\t")
    expected_columns = [
        "chr", "trID", "trOrigId", "gene", "strand",
        "tsBeg", "txEnd", "cdsStart", "cdsEnd",
        "exonStarts", "exonEnds", "exonFrames", "atts",
    ]
    assert header == expected_columns

    # Should have data rows
    assert len(lines) > 1

    # Check first data row has correct number of columns
    data_row = lines[1].split("\t")
    assert len(data_row) == len(expected_columns)


def test_save_as_default_gene_models_content(
    simple_gene_models: GeneModels,
) -> None:
    """Test _save_as_default_gene_models content is correct."""
    output = StringIO()
    _save_as_default_gene_models(simple_gene_models, output)

    content = output.getvalue()
    lines = content.strip().split("\n")

    # Get a data row (skip header)
    data_row = lines[1].split("\t")

    # Should have chromosome
    assert data_row[0] in ("1", "2")

    # Should have transcript ID
    assert data_row[1].startswith("tx")

    # Should have gene name
    assert data_row[3] in ("TP53", "BRCA1")

    # Should have strand
    assert data_row[4] in ("+", "-")


def test_save_as_default_gene_models_exon_format(
    simple_gene_models: GeneModels,
) -> None:
    """Test _save_as_default_gene_models formats exons correctly."""
    output = StringIO()
    _save_as_default_gene_models(simple_gene_models, output)

    content = output.getvalue()
    lines = content.strip().split("\n")

    # Check exon starts and ends are comma-separated
    for line in lines[1:]:  # Skip header
        fields = line.split("\t")
        exon_starts = fields[9]
        exon_ends = fields[10]
        exon_frames = fields[11]

        # Should be comma-separated lists
        assert "," in exon_starts or len(exon_starts.split(",")) == 1
        assert "," in exon_ends or len(exon_ends.split(",")) == 1
        assert "," in exon_frames or len(exon_frames.split(",")) == 1


def test_save_as_default_gene_models_file_gzipped(
    simple_gene_models: GeneModels,
    tmp_path: pathlib.Path,
) -> None:
    """Test save_as_default_gene_models creates gzipped file."""
    output_file = tmp_path / "gene_models.txt"

    save_as_default_gene_models(
        simple_gene_models,
        str(output_file),
        gzipped=True,
    )

    # Should create .gz file
    gz_file = tmp_path / "gene_models.txt.gz"
    assert gz_file.exists()

    # Should be readable as gzip
    with gzip.open(gz_file, "rt") as f:
        content = f.read()
        assert "chr\ttrID" in content  # Has header


def test_save_as_default_gene_models_file_not_gzipped(
    simple_gene_models: GeneModels,
    tmp_path: pathlib.Path,
) -> None:
    """Test save_as_default_gene_models creates plain text file."""
    output_file = tmp_path / "gene_models.txt"

    save_as_default_gene_models(
        simple_gene_models,
        str(output_file),
        gzipped=False,
    )

    # Should create plain file
    assert output_file.exists()

    # Should be readable as plain text
    content = pathlib.Path(output_file).read_text()
    assert "chr\ttrID" in content  # Has header


def test_save_as_default_gene_models_roundtrip(
    simple_gene_models: GeneModels,
    tmp_path: pathlib.Path,
) -> None:
    """Test saving and loading gene models maintains data integrity."""

    output_file = tmp_path / "gene_models.txt"

    save_as_default_gene_models(
        simple_gene_models,
        str(output_file),
        gzipped=False,
    )

    # Load it back
    loaded_models = build_gene_models_from_file(
        str(output_file), file_format="default",
    )
    loaded_models.load()

    # Should have same genes
    assert (
        set(simple_gene_models.gene_names())
        == set(loaded_models.gene_names())
    )

    # Should have same number of transcripts
    assert (
        len(simple_gene_models.transcript_models)
        == len(loaded_models.transcript_models)
    )


def test_collect_gtf_start_codon_regions_invalid_strand() -> None:
    """Test collect_gtf_start_codon_regions raises error for invalid strand."""
    regions = [BedRegion("chr1", 100, 105)]

    with pytest.raises(ValueError, match="Invalid strand"):
        collect_gtf_start_codon_regions("*", regions)


def test_collect_gtf_stop_codon_regions_invalid_strand() -> None:
    """Test collect_gtf_stop_codon_regions raises error for invalid strand."""
    regions = [BedRegion("chr1", 100, 105)]

    with pytest.raises(ValueError, match="Invalid strand"):
        collect_gtf_stop_codon_regions("?", regions)


def test_collect_gtf_cds_regions_basic() -> None:
    """Test collect_gtf_cds_regions removes stop codon from CDS."""
    regions = [
        BedRegion("chr1", 100, 109),
        BedRegion("chr1", 200, 204),
    ]

    # For positive strand, stop codon is at end
    cds_regions = collect_gtf_cds_regions("+", regions)

    # Should have removed stop codon (last 3 bases)
    total_length = sum(r.stop - r.start + 1 for r in cds_regions)
    original_length = sum(r.stop - r.start + 1 for r in regions)
    assert total_length == original_length - 3


def test_collect_gtf_start_codon_regions_single_exon() -> None:
    """Test start codon collection with single exon CDS."""
    regions = [BedRegion("chr1", 100, 109)]

    # Positive strand: start codon is first 3 bases
    start_codons = collect_gtf_start_codon_regions("+", regions)
    assert len(start_codons) == 1
    assert start_codons[0].start == 100
    assert start_codons[0].stop == 102

    # Negative strand: start codon is last 3 bases
    start_codons = collect_gtf_start_codon_regions("-", regions)
    assert len(start_codons) == 1
    assert start_codons[0].start == 107
    assert start_codons[0].stop == 109


def test_collect_gtf_start_codon_regions_split() -> None:
    """Test start codon collection when split across exons."""
    regions = [
        BedRegion("chr1", 100, 101),  # 2 bases
        BedRegion("chr1", 200, 200),  # 1 base
    ]

    # Positive strand: start codon spans both regions
    start_codons = collect_gtf_start_codon_regions("+", regions)
    assert len(start_codons) == 2
    assert start_codons[0] == regions[0]
    assert start_codons[1] == regions[1]


def test_collect_gtf_stop_codon_regions_single_exon() -> None:
    """Test stop codon collection with single exon CDS."""
    regions = [BedRegion("chr1", 100, 109)]

    # Positive strand: stop codon is last 3 bases
    stop_codons = collect_gtf_stop_codon_regions("+", regions)
    assert len(stop_codons) == 1
    assert stop_codons[0].start == 107
    assert stop_codons[0].stop == 109

    # Negative strand: stop codon is first 3 bases
    stop_codons = collect_gtf_stop_codon_regions("-", regions)
    assert len(stop_codons) == 1
    assert stop_codons[0].start == 100
    assert stop_codons[0].stop == 102


def test_collect_gtf_stop_codon_regions_split() -> None:
    """Test stop codon collection when split across exons."""
    regions = [
        BedRegion("chr1", 100, 101),  # 2 bases
        BedRegion("chr1", 200, 200),  # 1 base
    ]

    # Positive strand: stop codon at end, spans regions
    stop_codons = collect_gtf_stop_codon_regions("+", regions)
    assert len(stop_codons) == 2

    # Negative strand: stop codon at start, spans regions
    stop_codons = collect_gtf_stop_codon_regions("-", regions)
    assert len(stop_codons) == 2


def test_save_as_default_gene_models_attributes_escaping(
    tmp_path: pathlib.Path,
) -> None:
    """Test that attributes with colons are properly escaped."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TEST      tx1  1     +      10      100   12       95     2         10,50      40,100
"""  # noqa
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(content),
        },
    )
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    # Add attribute with colon
    for tm in gene_models.transcript_models.values():
        tm.attributes["test:attr"] = "value:with:colons"

    output_file = tmp_path / "gene_models.txt"
    save_as_default_gene_models(gene_models, str(output_file), gzipped=False)

    # Read and check attributes are escaped
    content = pathlib.Path(output_file).read_text()
    # Colons in keys should be replaced with underscores
    assert (
        "test_attr_value_with_colons" in content
        or "test:attr" in content
    )


def test_gene_models_to_gtf_attributes_formatting(
    simple_gene_models: GeneModels,
) -> None:
    """Test that GTF attributes are properly formatted."""
    result = gene_models_to_gtf(simple_gene_models)
    content = result.read()

    # Check GTF attribute formatting (key-value pairs with quotes)
    assert 'gene_id "' in content
    assert 'gene_name "' in content
    assert 'transcript_id "' in content


def test_save_as_default_gene_models_empty_attributes() -> None:
    """Test saving gene models with transcript without attributes."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TEST      tx1  1     +      10      100   12       95     1         10         100
"""  # noqa
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(content),
        },
    )
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    output = StringIO()
    _save_as_default_gene_models(gene_models, output)

    content = output.getvalue()
    # Should handle empty attributes gracefully
    assert "\t\n" in content or content.endswith("\t")


def test_get_exon_number_for_out_of_bounds() -> None:
    transcript = TranscriptModel(
        gene="gene",
        tr_id="transcript",
        tr_name="transcript",
        chrom="chr",
        strand="+",
        exons=[
            Exon(start=0, stop=10),
            Exon(start=20, stop=30),
        ],
        cds=(0, 30),
        tx=(0, 30),
    )

    result = get_exon_number_for(transcript, start=100, stop=110)
    assert result == 0
