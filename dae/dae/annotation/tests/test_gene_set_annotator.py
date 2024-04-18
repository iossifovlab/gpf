# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.gene_set_annotator import GeneSetAnnotator
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.testing import setup_directories
from dae.testing.foobar_import import foobar_genes, foobar_genome


@pytest.fixture(scope="module")
def test_grr(tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("test_grr")

    foobar_genome(root_path / "grr")
    foobar_genes(root_path / "grr")

    setup_directories(
        root_path, {
            "grr.yaml": textwrap.dedent(f"""
                id: reannotation_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "foobar_genome": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: genome
                        filename: chrAll.fa
                    """),
                },
                "foobar_genes": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: gene_models
                        filename: genes.txt
                        format: refflat
                    """),
                },
                "foobar_gene_set_collection": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        id: pesho
                        type: gene_set
                        format: directory
                        directory: geneSets
                    """),
                    "geneSets": {
                        "set_0.txt": textwrap.dedent("""set_0
                            random test gene set description
                            g1
                            g2
                        """),
                        "set_1.txt": textwrap.dedent("""set_1
                            random test gene set description
                            g1
                        """),
                        "set_2.txt": textwrap.dedent("""set_2
                            random test gene set description
                            g2
                        """),
                    },
                },
            },
        },
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml",
    ))


def test_gene_set_annotator(test_grr: GenomicResourceRepo) -> None:
    resource = test_grr.get_resource("foobar_gene_set_collection")
    annotator = GeneSetAnnotator(
        None, AnnotatorInfo("gosho", [], {}), resource, "set_0", "gene_list",
    )

    result = annotator.annotate(None, {"gene_list": ["g1"]})
    assert result == {"set_0": True}

    result = annotator.annotate(None, {"gene_list": ["g3"]})
    assert result == {"set_0": False}

    result = annotator.annotate(None, {"gene_list": ["g3", "g2"]})
    assert result == {"set_0": True}


def test_gene_score_annotator_used_context_attributes(
    test_grr: GenomicResourceRepo,
) -> None:
    resource = test_grr.get_resource("foobar_gene_set_collection")
    annotator = GeneSetAnnotator(
        None, AnnotatorInfo("gosho", [], {}), resource, "set_0", "gene_list",
    )

    assert annotator.used_context_attributes == ("gene_list",)


@pytest.mark.parametrize("set_id, chrom,pos,ref,alt, expected", [
    ("set_0", "foo", 10, "A", "C", True),
    ("set_0", "bar", 15, "A", "C", True),
    ("set_0", "foo", 20, "C", "G", False),
    ("set_1", "foo", 10, "C", "G", True),
    ("set_1", "bar", 15, "A", "C", False),
    ("set_1", "foo", 20, "C", "G", False),
    ("set_2", "bar", 15, "A", "C", True),
    ("set_2", "foo", 15, "A", "C", False),
    ("set_2", "bar", 20, "C", "G", False),
])
def test_gene_set_annotator_in_pipeline(
    # tmp_path_factory: pytest.TempPathFactory,
    test_grr: GenomicResourceRepo,
    set_id: str,
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    expected: bool,
) -> None:
    pipeline = build_annotation_pipeline(pipeline_config_str=textwrap.dedent(
        f"""
        - effect_annotator:
            genome: foobar_genome
            gene_models: foobar_genes
        - gene_set_annotator:
            resource_id: foobar_gene_set_collection
            gene_set_id: {set_id}
            input_gene_list: gene_list
        """),
        grr_repository=test_grr)

    allele = VCFAllele(chrom, pos, ref, alt)
    result = pipeline.annotate(allele)
    assert result[set_id] is expected
