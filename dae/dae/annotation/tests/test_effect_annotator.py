# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
import textwrap

import pytest

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_gene_models,
    setup_genome,
)
from dae.testing.t4c8_import import GENOME_CONTENT, GMM_CONTENT


@pytest.fixture()
def grr(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    setup_genome(tmp_path / "t4c8_genome" / "chrAll.fa", GENOME_CONTENT)
    setup_genome(tmp_path / "t4c8_genome_implicit_A" / "chrAll.fa",
                 GENOME_CONTENT)
    setup_genome(tmp_path / "t4c8_genome_implicit_B" / "chrAll.fa",
                 GENOME_CONTENT)

    setup_gene_models(
        tmp_path / "t4c8_genes" / "genes.txt",
        GMM_CONTENT,
        config=textwrap.dedent("""
            type: gene_models
            filename: genes.txt
            format: refflat
            meta:
              labels:
                reference_genome: t4c8_genome_implicit_A
        """))

    setup_gene_models(
        tmp_path / "t4c8_genes_ALT" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")

    return build_filesystem_test_repository(tmp_path)


def test_effect_annotator_resources(grr: GenomicResourceRepo) -> None:
    genome = "t4c8_genome"
    gene_models = "t4c8_genes"
    config = textwrap.dedent(f"""
        - effect_annotator:
            genome: {genome}
            gene_models: {gene_models}
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            genome,
            gene_models,
        }


def test_effect_annotator_documentation(grr: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
        - effect_annotator:
            genome: t4c8_genome
            gene_models: t4c8_genes
        """)
    pipeline = load_pipeline_from_yaml(pipeline_config, grr)
    att = pipeline.get_attribute_info("worst_effect")
    assert att is not None
    assert "Worst" in att.documentation


def test_effect_annotator_implicit_genome_from_gene_models(
    grr: GenomicResourceRepo,
) -> None:
    genome = "t4c8_genome_implicit_A"
    gene_models = "t4c8_genes"
    config = textwrap.dedent(f"""
        - effect_annotator:
            gene_models: {gene_models}
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            genome,
            gene_models,
        }


def test_effect_annotator_implicit_genome_from_preamble(
    grr: GenomicResourceRepo,
) -> None:
    genome = "t4c8_genome_implicit_B"
    gene_models = "t4c8_genes_ALT"
    config = textwrap.dedent(f"""
        preamble:
          input_reference_genome: {genome}
        annotators:
          - effect_annotator:
              gene_models: {gene_models}
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            genome,
            gene_models,
        }
