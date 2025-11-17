# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Tests for dae.genomic_resources.gene_models.gene_models_factory module."""
import pathlib
from typing import Any
from unittest.mock import Mock, patch

import pytest
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.genomic_resources.gene_models.gene_models_factory import (
    _INMEMORY_CACHE,
    build_gene_models_from_file,
    build_gene_models_from_resource,
    build_gene_models_from_resource_id,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    build_inmemory_test_resource,
    convert_to_tab_separated,
)

# Sample gene model content in refflat format
REFFLAT_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
BRCA1     tx2  17    -      200     300   210      290    2         200,250    220,300
POGZ      tx3  1     +      500     600   510      590    1         500        600
"""  # noqa

# Construct GTF content programmatically to avoid long lines
_GTF_BASE = "1\ttest\t{}\t{}\t{}\t.\t+\t{}\t"
_GTF_ATTRS = 'gene_id "TP53"; gene_name "TP53"; transcript_id "tx1";'
GTF_LINES = [
    _GTF_BASE.format("transcript", "10", "100", ".") + _GTF_ATTRS,
    _GTF_BASE.format("exon", "10", "15", ".") + _GTF_ATTRS,
    _GTF_BASE.format("exon", "50", "60", ".") + _GTF_ATTRS,
    _GTF_BASE.format("exon", "70", "100", ".") + _GTF_ATTRS,
    _GTF_BASE.format("CDS", "12", "15", "0") + _GTF_ATTRS,
    _GTF_BASE.format("CDS", "50", "60", "0") + _GTF_ATTRS,
    _GTF_BASE.format("CDS", "70", "95", "2") + _GTF_ATTRS,
]
GTF_CONTENT = "\n".join(GTF_LINES) + "\n"


@pytest.fixture(autouse=True)
def clear_cache() -> Any:
    """Clear the inmemory cache before and after each test."""
    _INMEMORY_CACHE.clear()
    yield
    _INMEMORY_CACHE.clear()


@pytest.fixture
def temp_gene_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a temporary gene model file."""
    gene_file = tmp_path / "genes.txt"
    gene_file.write_text(convert_to_tab_separated(REFFLAT_CONTENT))
    return gene_file


@pytest.fixture
def temp_gtf_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a temporary GTF file."""
    gtf_file = tmp_path / "genes.gtf"
    gtf_file.write_text(GTF_CONTENT)
    return gtf_file


@pytest.fixture
def temp_mapping_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a temporary gene mapping file."""
    mapping_file = tmp_path / "mapping.txt"
    mapping_file.write_text(convert_to_tab_separated("""
        from   to
        TP53   P53
        BRCA1  BC1
    """))
    return mapping_file


def test_build_from_file_basic(
    temp_gene_file: pathlib.Path,
) -> None:
    """Test basic loading from file."""
    gene_models = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert len(gene_models.transcript_models) == 3
    assert set(gene_models.gene_names()) == {"TP53", "BRCA1", "POGZ"}


def test_build_from_file_with_explicit_format(
    temp_gtf_file: pathlib.Path,
) -> None:
    """Test loading with explicit file format."""
    gene_models = build_gene_models_from_file(
        str(temp_gtf_file),
        file_format="gtf",
    )
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert len(gene_models.transcript_models) == 1
    assert "TP53" in gene_models.gene_names()


def test_build_from_file_with_gene_mapping(
    temp_gene_file: pathlib.Path,
    temp_mapping_file: pathlib.Path,
) -> None:
    """Test loading with gene mapping file."""
    gene_models = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
        gene_mapping_file_name=str(temp_mapping_file),
    )
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert set(gene_models.gene_names()) == {"P53", "BC1", "POGZ"}
    # Original names should not exist
    assert "TP53" not in gene_models.gene_names()
    assert "BRCA1" not in gene_models.gene_names()


def test_build_from_file_caching(
    temp_gene_file: pathlib.Path,
) -> None:
    """Test that repeated calls return cached instance."""
    gene_models1 = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )
    gene_models2 = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )

    # Should be the same object
    assert gene_models1 is gene_models2
    assert len(_INMEMORY_CACHE) == 1


def test_build_from_file_different_files_different_cache(
    temp_gene_file: pathlib.Path,
    temp_gtf_file: pathlib.Path,
) -> None:
    """Test that different files create different cache entries."""
    gene_models1 = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )
    gene_models2 = build_gene_models_from_file(
        str(temp_gtf_file),
        file_format="gtf",
    )

    # Should be different objects
    assert gene_models1 is not gene_models2
    assert len(_INMEMORY_CACHE) == 2


def test_build_from_file_without_format(
    temp_gene_file: pathlib.Path,
) -> None:
    """Test loading without explicit format (format inference)."""
    gene_models = build_gene_models_from_file(str(temp_gene_file))
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    # Should infer refflat format
    assert len(gene_models.transcript_models) == 3


def test_build_from_resource_basic() -> None:
    """Test basic loading from resource."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert len(gene_models.transcript_models) == 3
    assert set(gene_models.gene_names()) == {"TP53", "BRCA1", "POGZ"}


def test_build_from_resource_with_gene_mapping(
) -> None:
    """Test loading from resource with gene mapping."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat, "
                "gene_mapping: mapping.txt}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
            "mapping.txt": convert_to_tab_separated("""
                from   to
                TP53   P53
                BRCA1  BC1
            """),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert set(gene_models.gene_names()) == {"P53", "BC1", "POGZ"}


def test_build_from_resource_none_raises_error(
) -> None:
    """Test that passing None resource raises ValueError."""
    with pytest.raises(ValueError, match="missing resource"):
        build_gene_models_from_resource(None)


def test_build_from_resource_wrong_type_raises_error(
) -> None:
    """Test that wrong resource type raises ValueError."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml": "{type: position_score}",
            "data.txt": "some data",
        })

    with pytest.raises(ValueError, match="wrong resource type"):
        build_gene_models_from_resource(res)


def test_build_from_resource_caching() -> None:
    """Test that repeated calls return cached instance."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models1 = build_gene_models_from_resource(res)
    gene_models2 = build_gene_models_from_resource(res)

    # Should be the same object
    assert gene_models1 is gene_models2
    assert len(_INMEMORY_CACHE) == 1


def test_build_from_resource_different_resources_different_cache(
) -> None:
    """Test that different resources create different cache entries."""
    res1 = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes1.txt, format: refflat}",
            "genes1.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    res2 = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes2.txt, format: refflat}",
            "genes2.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    build_gene_models_from_resource(res1)
    build_gene_models_from_resource(res2)

    # Different resources should create different cache entries
    assert len(_INMEMORY_CACHE) == 2


def test_build_from_resource_id_basic() -> None:
    """Test basic loading from resource ID."""
    grr = build_inmemory_test_repository({
        "test_models": {
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        },
    })

    gene_models = build_gene_models_from_resource_id("test_models", grr)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert len(gene_models.transcript_models) == 3
    assert set(gene_models.gene_names()) == {"TP53", "BRCA1", "POGZ"}


def test_build_from_resource_id_with_mapping(
) -> None:
    """Test loading from resource ID with gene mapping."""
    grr = build_inmemory_test_repository({
        "test_models": {
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat, "
                "gene_mapping: mapping.txt}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
            "mapping.txt": convert_to_tab_separated("""
                from   to
                TP53   P53
            """),
        },
    })

    gene_models = build_gene_models_from_resource_id("test_models", grr)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert "P53" in gene_models.gene_names()
    assert "TP53" not in gene_models.gene_names()


def test_build_from_resource_id_without_grr() -> None:
    """Test that build_from_resource_id can use default repository."""
    # This test mocks the default repository creation
    mock_grr = Mock()
    mock_resource = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })
    mock_grr.get_resource.return_value = mock_resource

    with patch(
        "dae.genomic_resources.repository_factory."
        "build_genomic_resource_repository",
        return_value=mock_grr,
    ):
        gene_models = build_gene_models_from_resource_id("test_models")
        gene_models.load()

        assert isinstance(gene_models, GeneModels)
        mock_grr.get_resource.assert_called_once_with("test_models")


def test_build_from_resource_id_caching() -> None:
    """Test that repeated calls return cached instance."""
    grr = build_inmemory_test_repository({
        "test_models": {
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        },
    })

    gene_models1 = build_gene_models_from_resource_id("test_models", grr)
    gene_models2 = build_gene_models_from_resource_id("test_models", grr)

    # Should be the same object
    assert gene_models1 is gene_models2
    assert len(_INMEMORY_CACHE) == 1


def test_build_from_resource_id_nonexistent_resource(
) -> None:
    """Test that requesting nonexistent resource raises error."""
    grr = build_inmemory_test_repository({
        "test_models": {
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        },
    })

    with pytest.raises(
        FileNotFoundError, match=r"resource.*nonexistent_models.*not found",
    ):
        build_gene_models_from_resource_id("nonexistent_models", grr)


def test_cache_isolation_between_functions(
    temp_gene_file: pathlib.Path,
) -> None:
    """Test that cache is shared across all factory functions."""
    # Build from file
    gene_models1 = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )

    # Build from resource with same underlying file
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })
    gene_models2 = build_gene_models_from_resource(res)

    # Different cache entries since they have different cache keys
    assert gene_models1 is not gene_models2
    assert len(_INMEMORY_CACHE) == 2


def test_cache_key_includes_filename_and_repo_url(
) -> None:
    """Test that cache key includes both filename and repo URL."""
    res1 = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes1.txt, format: refflat}",
            "genes1.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    res2 = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes2.txt, format: refflat}",
            "genes2.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    build_gene_models_from_resource(res1)
    build_gene_models_from_resource(res2)

    # Different resources create different cache entries
    assert len(_INMEMORY_CACHE) == 2


def test_build_from_file_with_all_parameters(
    temp_gene_file: pathlib.Path,
    temp_mapping_file: pathlib.Path,
) -> None:
    """Test build_from_file with all optional parameters."""
    gene_models = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
        gene_mapping_file_name=str(temp_mapping_file),
    )
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert "P53" in gene_models.gene_names()
    assert "BC1" in gene_models.gene_names()
    assert "TP53" not in gene_models.gene_names()


def test_build_from_resource_returns_unloaded_gene_models(
) -> None:
    """Test that factory returns unloaded GeneModels instance."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models = build_gene_models_from_resource(res)

    # Should not be loaded initially
    assert not gene_models.is_loaded()

    # Should be able to load
    gene_models.load()
    assert gene_models.is_loaded()


def test_build_from_file_returns_unloaded_gene_models(
    temp_gene_file: pathlib.Path,
) -> None:
    """Test that factory returns unloaded GeneModels instance."""
    gene_models = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )

    # Should not be loaded initially
    assert not gene_models.is_loaded()

    # Should be able to load
    gene_models.load()
    assert gene_models.is_loaded()


def test_cached_instance_remains_loaded(
    temp_gene_file: pathlib.Path,
) -> None:
    """Test that cached instance retains loaded state."""
    gene_models1 = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )
    gene_models1.load()

    # Get cached instance
    gene_models2 = build_gene_models_from_file(
        str(temp_gene_file),
        file_format="refflat",
    )

    # Should be same instance and already loaded
    assert gene_models1 is gene_models2
    assert gene_models2.is_loaded()
