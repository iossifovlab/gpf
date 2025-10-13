# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
    TranscriptModel,
    build_gene_models_from_resource,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)

# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx2  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
BRCA1     tx4  1     +      200     300   210      290    2         200,250    220,300
EGFR      tx5  2     -      50      150   60       140    3         50,80,120  70,90,150
"""  # noqa


@pytest.fixture
def sample_gene_models() -> GeneModels:
    """Create a sample GeneModels instance for testing."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()
    return gene_models


def test_gene_models_by_location_single_position(
    sample_gene_models: GeneModels,
) -> None:
    """Test finding gene models at a single position."""
    # Test position within TP53 transcript
    results = sample_gene_models.gene_models_by_location("1", 50)
    assert len(results) == 2
    gene_names = {tm.gene for tm in results}
    assert "TP53" in gene_names

    # Test position within BRCA1 transcript
    results = sample_gene_models.gene_models_by_location("1", 250)
    assert len(results) == 1
    assert results[0].gene == "BRCA1"
    assert results[0].tr_id == "tx4_1"

    # Test position within EGFR transcript on different chromosome
    results = sample_gene_models.gene_models_by_location("2", 80)
    assert len(results) == 1
    assert results[0].gene == "EGFR"
    assert results[0].tr_id == "tx5_1"


def test_gene_models_by_location_no_matches(
    sample_gene_models: GeneModels,
) -> None:
    """Test finding gene models when no transcripts overlap the position."""
    # Position between TP53/BRCA1 and BRCA1 on chromosome 1
    results = sample_gene_models.gene_models_by_location("1", 150)
    assert len(results) == 0

    # Position before all transcripts
    results = sample_gene_models.gene_models_by_location("1", 5)
    assert len(results) == 0

    # Position after all transcripts
    results = sample_gene_models.gene_models_by_location("1", 400)
    assert len(results) == 0

    # Non-existent chromosome
    results = sample_gene_models.gene_models_by_location("99", 50)
    assert len(results) == 0


def test_gene_models_by_location_range_overlapping(
    sample_gene_models: GeneModels,
) -> None:
    """Test finding gene models with a range that overlaps transcripts."""
    # Range that covers both TP53 transcripts and BRCA1
    results = sample_gene_models.gene_models_by_location("1", 50, 250)
    assert len(results) == 3
    gene_names = {tm.gene for tm in results}
    assert "TP53" in gene_names
    assert "BRCA1" in gene_names

    # Range that only overlaps TP53 transcripts
    results = sample_gene_models.gene_models_by_location("1", 10, 100)
    assert len(results) == 2
    assert all(tm.gene == "TP53" for tm in results)

    # Range that partially overlaps BRCA1
    results = sample_gene_models.gene_models_by_location("1", 190, 210)
    assert len(results) == 1
    assert results[0].gene == "BRCA1"


def test_gene_models_by_location_range_no_overlap(
    sample_gene_models: GeneModels,
) -> None:
    """Test finding gene models with non-overlapping range."""
    # Range between TP53 and BRCA1
    results = sample_gene_models.gene_models_by_location("1", 120, 180)
    assert len(results) == 0

    # Range after all transcripts on chromosome 1
    results = sample_gene_models.gene_models_by_location("1", 350, 400)
    assert len(results) == 0

    # Range before all transcripts on chromosome 2
    results = sample_gene_models.gene_models_by_location("2", 10, 40)
    assert len(results) == 0


def test_gene_models_by_location_range_swapped_positions(
    sample_gene_models: GeneModels,
) -> None:
    """Test that method handles swapped pos1/pos2 correctly."""
    # Normal order
    results1 = sample_gene_models.gene_models_by_location("1", 50, 250)

    # Swapped order (should give same results)
    results2 = sample_gene_models.gene_models_by_location("1", 250, 50)

    assert len(results1) == len(results2)
    assert len(results1) == 3

    # Results should contain the same transcripts
    tr_ids1 = {tm.tr_id for tm in results1}
    tr_ids2 = {tm.tr_id for tm in results2}
    assert tr_ids1 == tr_ids2


def test_gene_models_by_location_edge_cases(
    sample_gene_models: GeneModels,
) -> None:
    """Test edge cases like exact boundaries."""
    # Test exact start position of TP53
    results = sample_gene_models.gene_models_by_location("1", 11)
    assert len(results) == 2
    assert all(tm.gene == "TP53" for tm in results)

    # Test exact end position of TP53
    results = sample_gene_models.gene_models_by_location("1", 100)
    assert len(results) == 2
    assert all(tm.gene == "TP53" for tm in results)

    # Test exact start position of BRCA1
    results = sample_gene_models.gene_models_by_location("1", 201)
    assert len(results) == 1
    assert results[0].gene == "BRCA1"

    # Test exact end position of BRCA1
    results = sample_gene_models.gene_models_by_location("1", 300)
    assert len(results) == 1
    assert results[0].gene == "BRCA1"


def test_gene_models_by_location_range_touching_boundaries(
    sample_gene_models: GeneModels,
) -> None:
    """Test ranges that touch transcript boundaries."""
    # Range that touches the start of TP53
    results = sample_gene_models.gene_models_by_location("1", 5, 11)
    assert len(results) == 2
    assert all(tm.gene == "TP53" for tm in results)

    # Range that touches the end of TP53
    results = sample_gene_models.gene_models_by_location("1", 100, 110)
    assert len(results) == 2
    assert all(tm.gene == "TP53" for tm in results)

    # Range that exactly spans one transcript
    results = sample_gene_models.gene_models_by_location("1", 200, 300)
    assert len(results) == 1
    assert results[0].gene == "BRCA1"


def test_gene_models_by_location_different_chromosomes(
    sample_gene_models: GeneModels,
) -> None:
    """Test that method correctly handles different chromosomes."""
    # Get all models on chromosome 1
    results_chr1 = sample_gene_models.gene_models_by_location("1", 1, 1000)
    chr1_genes = {tm.gene for tm in results_chr1}
    assert "TP53" in chr1_genes
    assert "BRCA1" in chr1_genes
    assert "EGFR" not in chr1_genes

    # Get all models on chromosome 2
    results_chr2 = sample_gene_models.gene_models_by_location("2", 1, 1000)
    chr2_genes = {tm.gene for tm in results_chr2}
    assert "EGFR" in chr2_genes
    assert "TP53" not in chr2_genes
    assert "BRCA1" not in chr2_genes

    # Get models on chromosome 17 (POGZ)
    results_chr17 = sample_gene_models.gene_models_by_location("17", 1, 1000)
    chr17_genes = {tm.gene for tm in results_chr17}
    assert "POGZ" in chr17_genes
    assert len(chr17_genes) == 1


def test_gene_models_by_location_multiple_transcripts_same_gene(
    sample_gene_models: GeneModels,
) -> None:
    """Test that method returns multiple transcripts for the same gene."""
    # Position that should hit both TP53 transcripts
    results = sample_gene_models.gene_models_by_location("1", 50)
    tp53_transcripts = [tm for tm in results if tm.gene == "TP53"]

    assert len(tp53_transcripts) == 2
    tr_ids = {tm.tr_id for tm in tp53_transcripts}
    assert "tx1_1" in tr_ids
    assert "tx2_1" in tr_ids


def test_gene_models_by_location_return_transcript_details(
    sample_gene_models: GeneModels,
) -> None:
    """Test that returned TranscriptModel objects have correct details."""
    results = sample_gene_models.gene_models_by_location("1", 50)

    for tm in results:
        assert hasattr(tm, "gene")
        assert hasattr(tm, "tr_id")
        assert hasattr(tm, "tr_name")
        assert hasattr(tm, "chrom")
        assert hasattr(tm, "strand")
        assert hasattr(tm, "tx")
        assert hasattr(tm, "cds")

        # Verify the position 50 is within the transcript range
        assert tm.tx[0] <= 50 <= tm.tx[1]
        assert tm.chrom == "1"


@pytest.fixture
def tms_fixture() -> list[TranscriptModel]:
    return [
        TranscriptModel(
            "a1", "a", "a", "1", "+", tx=(10, 100), cds=(12, 95), exons=[],
        ),
        TranscriptModel(
            "c1", "c", "c", "2", "+", tx=(50, 200), cds=(60, 180), exons=[],
        ),
        TranscriptModel(
            "b1", "b", "b", "1", "-", tx=(150, 250), cds=(160, 240), exons=[],
        ),
    ]


@pytest.mark.parametrize(
    "pos_start, pos_end, expected_index",
    [
        (50, 50, 0),
        (10, 10, 0),
        (1, 9, -1),
        (1, 101, 0),

    ],
)
def test_search_tx(
    tms_fixture: list[TranscriptModel],
    pos_start: int,
    pos_end: int,
    expected_index: int,
) -> None:

    res = GeneModels._search_tx(tms_fixture, pos_start, pos_end)
    assert res == expected_index


@pytest.fixture
def tms_fixture1() -> list[TranscriptModel]:
    return [
        TranscriptModel(
            "aa1", "aa", "aa", "1", "-", tx=(1000, 2000),
            cds=(1060, 1960), exons=[],
        ),
        TranscriptModel(
            "bb1", "bb", "bb", "1", "-", tx=(1050, 1150),
            cds=(1060, 1140), exons=[],
        ),
        TranscriptModel(
            "cc1", "cc", "cc", "1", "-", tx=(1850, 1950),
            cds=(1860, 1940), exons=[],
        ),
    ]


def test_search_tx1(
    tms_fixture1: list[TranscriptModel],
) -> None:

    res = GeneModels._search_tx(tms_fixture1, 1100, 1900)
    assert res == 0
