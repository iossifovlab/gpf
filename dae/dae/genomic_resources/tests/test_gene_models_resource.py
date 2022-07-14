# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genomic_resources.gene_models import \
    load_gene_models_from_resource, GeneModels
from dae.genomic_resources.testing import build_test_resource
from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.repository import GenomicResourceProtocolRepo, \
    GenomicResource


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx1  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
"""  # noqa


def test_gene_models_resource_with_format():
    res = build_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)
        })

    gene_models = load_gene_models_from_resource(res)
    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_inferred_format():
    res = build_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)
        })

    gene_models = load_gene_models_from_resource(res)
    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource_with_inferred_format_and_gene_mapping():
    res = build_test_resource(
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

    gene_models = load_gene_models_from_resource(res)
    assert isinstance(gene_models, GeneModels)

    assert set(gene_models.gene_names()) == {"gosho", "pesho"}
    assert len(gene_models.transcript_models) == 3


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_against_against_different_repo_types(resource_builder, scheme):
    res = resource_builder(
        scheme=scheme,
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(GMM_CONTENT)
        })

    gene_models = load_gene_models_from_resource(res)
    assert set(gene_models.gene_names()) == {"TP53", "POGZ"}
    assert len(gene_models.transcript_models) == 3


def test_gene_models_resource(fixture_dirname):

    dirname = fixture_dirname("genomic_resources")
    proto = build_fsspec_protocol("d", dirname)
    repo = GenomicResourceProtocolRepo(proto)

    res = repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
        "gene_models/refGene_201309")

    assert res is not None
    assert isinstance(res, GenomicResource)

    gene_models = load_gene_models_from_resource(res)
    assert isinstance(gene_models, GeneModels)

    assert len(gene_models.gene_models) == 13
