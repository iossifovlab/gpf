# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
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
