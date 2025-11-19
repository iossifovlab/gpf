# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
)
from dae.genomic_resources.gene_models.gene_models_factory import (
    build_gene_models_from_resource,
    build_gene_models_from_resource_id,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    build_inmemory_test_resource,
    convert_to_tab_separated,
    resource_builder,
)

# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx1  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
"""  # noqa


def test_gene_models_resource_with_format() -> None:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_inferred_format() -> None:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_inferred_format_and_gene_mapping() -> None:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, "
                "gene_mapping: geneMap.txt}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
            "geneMap.txt": convert_to_tab_separated("""
                from   to
                POGZ   gosho
                TP53   pesho
            """),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"gosho", "pesho"}
    assert len(gene_models.transcript_models) == 3


@pytest.mark.parametrize("scheme", [
    "file",
    # "s3",
    "http",
])
def test_against_against_different_repo_types(scheme: str) -> None:
    with resource_builder(scheme, {
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)}) as res:

        gene_models = build_gene_models_from_resource(res)
        gene_models.load()

        assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
        assert len(gene_models.transcript_models) == 3


def test_build_gene_models_from_resource_id() -> None:
    grr = build_inmemory_test_repository({
        "example_models": {
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
        },
    })
    gene_models = build_gene_models_from_resource_id("example_models", grr)
    gene_models.load()
    assert isinstance(gene_models, GeneModels)
    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_chrom_mapping_add_prefix() -> None:
    """Test add_prefix chrom_mapping adds prefix to chromosomes."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml": """
                type: gene_models
                filename: genes.txt
                format: refflat
                chrom_mapping:
                    add_prefix: chr
            """,
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3

    # Check that chromosomes have the prefix added
    assert gene_models.has_chromosome("chr1")
    assert gene_models.has_chromosome("chr17")
    assert not gene_models.has_chromosome("1")
    assert not gene_models.has_chromosome("17")

    # Verify transcripts have mapped chromosomes
    for tm in gene_models.transcript_models.values():
        assert tm.chrom.startswith("chr")

    # Check gene models by location with mapped chromosome names
    tp53_models = gene_models.gene_models_by_location("chr1", 50)
    assert len(tp53_models) == 2
    assert all(tm.gene == "TP53" for tm in tp53_models)

    pogz_models = gene_models.gene_models_by_location("chr17", 50)
    assert len(pogz_models) == 1
    assert pogz_models[0].gene == "POGZ"


def test_gene_models_resource_with_chrom_mapping_del_prefix() -> None:
    """Test del_prefix chrom_mapping removes prefix from chromosomes."""
    # Content with chr prefix
    gmm_content_with_chr = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  chr1  +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx2  chr1  +      10      100   12       95     2         10,70      15,100
POGZ      tx3  chr17 +      10      100   12       95     3         10,50,70   15,60,100
"""  # noqa

    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml": """
                type: gene_models
                filename: genes.txt
                format: refflat
                chrom_mapping:
                    del_prefix: chr
            """,
            "genes.txt": convert_to_tab_separated(gmm_content_with_chr),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3

    # Check that chromosomes have the prefix removed
    assert gene_models.has_chromosome("1")
    assert gene_models.has_chromosome("17")
    assert not gene_models.has_chromosome("chr1")
    assert not gene_models.has_chromosome("chr17")

    # Verify transcripts have mapped chromosomes
    for tm in gene_models.transcript_models.values():
        assert not tm.chrom.startswith("chr")

    # Check gene models by location with mapped chromosome names
    tp53_models = gene_models.gene_models_by_location("1", 50)
    assert len(tp53_models) == 2
    assert all(tm.gene == "TP53" for tm in tp53_models)

    pogz_models = gene_models.gene_models_by_location("17", 50)
    assert len(pogz_models) == 1
    assert pogz_models[0].gene == "POGZ"


def test_gene_models_resource_with_chrom_mapping_filename() -> None:
    """Test that filename-based chrom_mapping correctly maps chromosomes."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml": """
                type: gene_models
                filename: genes.txt
                format: refflat
                chrom_mapping:
                    filename: chrom_map.txt
            """,
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
            "chrom_map.txt": """1\tchr1
17\tchr17
""",
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3

    # Check that chromosomes are mapped according to the file
    assert gene_models.has_chromosome("chr1")
    assert gene_models.has_chromosome("chr17")
    assert not gene_models.has_chromosome("1")
    assert not gene_models.has_chromosome("17")

    # Verify transcript chromosomes
    for tm in gene_models.transcript_models.values():
        assert tm.chrom.startswith("chr")

    # Check gene models by location with mapped chromosome names
    tp53_models = gene_models.gene_models_by_location("chr1", 50)
    assert len(tp53_models) == 2
    assert all(tm.gene == "TP53" for tm in tp53_models)

    pogz_models = gene_models.gene_models_by_location("chr17", 50)
    assert len(pogz_models) == 1
    assert pogz_models[0].gene == "POGZ"


def test_gene_models_resource_chrom_mapping_filters_unmapped() -> None:
    """Test that transcripts on unmapped chromosomes are filtered out."""
    # Mapping file that only maps chromosome 1, not 17
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml": """
                type: gene_models
                filename: genes.txt
                format: refflat
                chrom_mapping:
                    filename: chrom_map.txt
            """,
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
            "chrom_map.txt": """1\tchr1
""",  # Only map chromosome 1, not 17
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    # Only TP53 genes should remain (they are on chromosome 1)
    # POGZ is on chromosome 17 which is not mapped, so it should be filtered
    assert set(gene_models.gene_names()) == {"TP53"}
    assert len(gene_models.transcript_models) == 2

    # Check that only chr1 exists
    assert gene_models.has_chromosome("chr1")
    assert not gene_models.has_chromosome("chr17")
    assert not gene_models.has_chromosome("1")
    assert not gene_models.has_chromosome("17")

    # Verify all remaining transcripts are on chr1
    for tm in gene_models.transcript_models.values():
        assert tm.chrom == "chr1"


def test_gene_models_resource_chrom_mapping_with_gene_mapping() -> None:
    """Test that chrom_mapping and gene_mapping work together correctly."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml": """
                type: gene_models
                filename: genes.txt
                format: refflat
                gene_mapping: geneMap.txt
                chrom_mapping:
                    add_prefix: chr
            """,
            "genes.txt": convert_to_tab_separated(GMM_CONTENT),
            "geneMap.txt": convert_to_tab_separated("""
                from   to
                POGZ   gosho
                TP53   pesho
            """),
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    # Check gene names are mapped
    assert set(gene_models.gene_names()) == {"gosho", "pesho"}
    assert len(gene_models.transcript_models) == 3

    # Check chromosomes have prefix
    assert gene_models.has_chromosome("chr1")
    assert gene_models.has_chromosome("chr17")

    # Verify both mappings are applied
    for tm in gene_models.transcript_models.values():
        assert tm.chrom.startswith("chr")
        assert tm.gene in {"gosho", "pesho"}

    # Check gene models by location with mapped chromosome names
    pesho_models = gene_models.gene_models_by_location("chr1", 50)
    assert len(pesho_models) == 2
    assert all(tm.gene == "pesho" for tm in pesho_models)

    gosho_models = gene_models.gene_models_by_location("chr17", 50)
    assert len(gosho_models) == 1
    assert gosho_models[0].gene == "gosho"
