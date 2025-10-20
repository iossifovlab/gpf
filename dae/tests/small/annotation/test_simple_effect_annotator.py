# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
from dae.annotation.annotatable import Annotatable, Position, Region, VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.simple_effect_annotator import SimpleEffectAnnotator
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    convert_to_tab_separated,
)


@pytest.fixture(scope="module")
def grr() -> GenomicResourceProtocolRepo:
    return build_inmemory_test_repository({
        "gene_models": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: gene_models
                filename: gene_models.tsv
                format: "refflat"
            """),

            "gene_models.tsv": convert_to_tab_separated("""
                #geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds 
                g1        tx1  foo   +      3       17    3        17     2         3,13       6,17
                g11       tx2  foo   +      3       9     3        6      1         3          6
                g4        tx4  foo   -      20      40    25       35     1         25         35
                g5        tx5  foo   -      25      35    27       35     1         27         35
                g6        tx6  foo   -      50      80    55       71     2         55,65      61,71
                g2        tx3  bar   -      3       20    3        15     1         3          17
                """)  # noqa
        },
    })


@pytest.mark.parametrize("annotatable, effect, genes", [
    (Position("foo", 2), "intergenic", ""),
    (Position("foo", 7), "intercoding_intronic", "g1"),
    (Position("foo", 14), "coding", "g1"),
    (Position("bar", 16), "peripheral", "g2"),
    (Region("bar", 14, 20), "coding", "g2"),
    (Region("bar", 16, 20), "peripheral", "g2"),
    (VCFAllele("bar", 16, "AACC", "A"), "peripheral", "g2"),
])
def test_basic(
    annotatable: Annotatable,
    effect: str,
    genes: str,
    grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
            """),
        grr)

    atts = pipeline.annotate(annotatable)
    assert atts["worst_effect"] == effect
    assert atts["worst_effect_genes"] == genes


@pytest.mark.parametrize("chrom, pos, pos_end, expected", [
    ("foo", 15, 15, {"coding": {"g1"}}),
    ("foo", 10, 14, {"coding": {"g1"}, "intercoding_intronic": {"g1"}}),
    ("foo", 28, 28, {"coding": {"g4", "g5"}}),
    ("foo", 41, 42, {"intergenic": set()}),
    ("foo", 26, 26, {"coding": {"g4"}, "peripheral": {"g5"}}),
    ("foo", 50, 50, {"intergenic": set()}),
    ("foo", 51, 51, {"peripheral": {"g6"}}),
    ("foo", 72, 72, {"peripheral": {"g6"}}),
    ("foo", 55, 55, {"peripheral": {"g6"}}),
    ("foo", 56, 56, {"coding": {"g6"}}),
    ("foo", 62, 62, {"intercoding_intronic": {"g6"}}),
    ("foo", 65, 65, {"intercoding_intronic": {"g6"}}),
    ("foo", 66, 66, {"coding": {"g6"}}),
])
def test_run_annotate(
    chrom: str,
    pos: int,
    pos_end: int,
    expected: dict[str, set[str]],
    grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
            """),
        grr)

    with pipeline.open() as pipeline:
        sea = pipeline.annotators[0]
        assert isinstance(sea, SimpleEffectAnnotator)

        result = sea.run_annotate(chrom, pos, pos_end)
        assert result == expected


@pytest.mark.parametrize(
    "annotatable, effect, genes, all_genes,gene_effects", [
        (Position("foo", 2), "intergenic", "", "", ""),
        (Position("foo", 7), "intercoding_intronic", "g1", "g1,g11",
         "g1:intercoding_intronic|g11:peripheral"),
        (Position("foo", 14), "coding", "g1", "g1", "g1:coding"),
    ],
)
def test_full_annotation(
    annotatable: Annotatable,
    effect: str,
    genes: str,
    all_genes: str,
    gene_effects: str,
    grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
                attributes:
                - worst_effect
                - worst_effect_genes
                - worst_effect_gene_list
                - gene_list
                - genes
                - gene_effects
                - coding_gene_list
                - coding_genes
                - peripheral_gene_list
                - peripheral_genes
                - intercoding_intronic_gene_list
                - intercoding_intronic_genes
            """),
        grr)

    atts = pipeline.annotate(annotatable)
    assert atts["worst_effect"] == effect
    assert atts["worst_effect_genes"] == genes
    assert atts["genes"] == all_genes
    assert atts["gene_effects"] == gene_effects
