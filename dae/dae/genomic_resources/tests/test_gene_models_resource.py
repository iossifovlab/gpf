# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import pytest

from dae.genomic_resources.gene_models import \
    build_gene_models_from_resource, GeneModels
from dae.genomic_resources.testing import \
    build_inmemory_test_resource, convert_to_tab_separated, \
    build_filesystem_test_repository, resource_builder
from dae.genomic_resources.repository import \
    GenomicResource


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx1  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
"""  # noqa


def test_gene_models_resource_with_format():
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_inferred_format():
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_inferred_format_and_gene_mapping():
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
            """)
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"gosho", "pesho"}
    assert len(gene_models.transcript_models) == 3


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_against_against_different_repo_types(scheme):
    with resource_builder(scheme, {
            "genomic_resource.yaml":
            "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)}) as res:

        gene_models = build_gene_models_from_resource(res)
        gene_models.load()

        assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
        assert len(gene_models.transcript_models) == 3


def test_gene_models_resource(fixture_dirname):

    dirname = fixture_dirname("genomic_resources")
    repo = build_filesystem_test_repository(pathlib.Path(dirname))

    res = repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
        "gene_models/refGene_201309")

    assert res is not None
    assert isinstance(res, GenomicResource)

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert isinstance(gene_models, GeneModels)
    assert gene_models.gene_models is not None
    assert len(gene_models.gene_models) == 13
