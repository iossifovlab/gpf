# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
import textwrap
from typing import Any

import pytest
import pytest_mock
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.effect_annotation.effect import AnnotationEffect
from dae.genomic_resources.genomic_context_base import (
    SimpleGenomicContext,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_gene_models,
    setup_genome,
)
from dae.testing.t4c8_import import GENOME_CONTENT, GMM_CONTENT


@pytest.fixture
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


def test_effect_annotator_implicit_genome_from_context(
    mocker: pytest_mock.MockerFixture,
    grr: GenomicResourceRepo,
) -> None:
    genome_id = "t4c8_genome_implicit_B"
    gene_models = "t4c8_genes_ALT"
    config = textwrap.dedent(f"""
        - effect_annotator:
            gene_models: {gene_models}
        """)

    genome = build_reference_genome_from_resource_id(genome_id, grr)
    context = SimpleGenomicContext(
        context_objects={"reference_genome": genome}, source="test_context")
    mocker.patch(
        "dae.annotation.utils.get_genomic_context",
    ).return_value = context

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            genome_id,
            gene_models,
        }


@pytest.mark.parametrize(
    "effects, target_gene_list, expected_gene_list", [
        (["CNV+", "frame-shift"], "CNV", ["gene1"]),
        (["frame-shift", "CNV+"], "CNV", ["gene2"]),
        (["CNV-", "CNV+"], "CNV", ["gene1", "gene2"]),
        (["CNV-", "CNV+"], "CNV+", ["gene2"]),
        (["nonsense", "CNV+"], "coding", ["gene1"]),
        (["nonsense", "CNV+"], "nonsynonymous", ["gene1"]),
        (["intron", "CNV+"], "noncoding", ["gene1"]),
        (["frame-shift", "CNV+"], "LGDs", ["gene1"]),
        (["3'UTR", "CNV+"], "UTRs", ["gene1"]),
        (["3'UTR", "CNV+"], "3'UTR", ["gene1"]),
        (["3'UTR-intron", "CNV+"], "3'UTR-intron", ["gene1"]),
        (["5'UTR", "CNV+"], "5'UTR", ["gene1"]),
        (["5'UTR-intron", "CNV+"], "5'UTR-intron", ["gene1"]),
        (["frame-shift", "CNV+"], "frame-shift", ["gene1"]),
        (["intergenic", "CNV+"], "intergenic", ["gene1"]),
        (["intron", "CNV+"], "intron", ["gene1"]),
        (["missense", "CNV+"], "missense", ["gene1"]),
        (["no-frame-shift", "CNV+"], "no-frame-shift", ["gene1"]),
        (
            ["no-frame-shift-newStop", "CNV+"],
            "no-frame-shift-newStop", ["gene1"],
        ),
        (["noEnd", "CNV+"], "noEnd", ["gene1"]),
        (["noStart", "CNV+"], "noStart", ["gene1"]),
        (["non-coding", "CNV+"], "non-coding", ["gene1"]),
        (["non-coding-intron", "CNV+"], "non-coding-intron", ["gene1"]),
        (["nonsense", "CNV+"], "nonsense", ["gene1"]),
        (["splice-site", "CNV+"], "splice-site", ["gene1"]),
        (["synonymous", "CNV+"], "synonymous", ["gene1"]),
        (["CDS", "CNV+"], "CDS", ["gene1"]),
        (["CNV-", "CNV+"], "CNV-", ["gene1"]),
    ],
)
def test_effect_annotator_gene_lists(
    mocker: pytest_mock.MockerFixture,
    grr: GenomicResourceRepo,
    effects: list[str],
    target_gene_list: str,
    expected_gene_list: list[str],
) -> None:
    genome_id = "t4c8_genome_implicit_B"
    gene_models = "t4c8_genes_ALT"
    config = textwrap.dedent(f"""
        - effect_annotator:
            gene_models: {gene_models}
            genome: {genome_id}
            attributes:
              - gene_list
              - {target_gene_list}_gene_list
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    annotation_effects = [
        AnnotationEffect(effect) for effect in effects
    ]

    for idx, eff in enumerate(annotation_effects, start=1):
        eff.gene = f"gene{idx}"

    with annotation_pipeline.open() as pipeline:
        annotate_context: dict[str, Any] = {}
        annotator = pipeline.annotators[0]
        mocker.patch.object(
            annotator.effect_annotator, "annotate_allele",  # type: ignore
            return_value=annotation_effects,
        )
        annotatable = VCFAllele("chr1", 1, "A", "T")
        result = annotator.annotate(annotatable, annotate_context)
        assert result[f"{target_gene_list}_gene_list"] == expected_gene_list


@pytest.mark.parametrize(
    "attribute, expected", [
        ("worst_effect", False),
        ("gene_effects", False),
        ("worst_effect_genes", False),
        ("worst_effect_gene_list", True),
    ],
)
def test_effect_annotator_attributes(
    grr: GenomicResourceRepo,
    attribute: str,
    expected: bool,  # noqa: FBT001
) -> None:
    genome = "t4c8_genome"
    gene_models = "t4c8_genes"
    config = textwrap.dedent(f"""
        - effect_annotator:
            genome: {genome}
            gene_models: {gene_models}
            attributes:
              - {attribute}
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]

        assert len(annotator.attributes) == 1
        attr = annotator.attributes[0]
        assert attr.name == attribute
        assert attr.internal == expected
