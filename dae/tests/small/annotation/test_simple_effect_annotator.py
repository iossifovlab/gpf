# pylint: disable=W0621,C0114,C0116,W0212,W0613,R0917
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
                g1        tx2  foo   +      3       9     3        6      1         3          6
                g4        tx4  foo   -      20      40    25       35     1         25         35
                g5        tx5  foo   -      25      35    27       35     1         27         35
                g6        tx6  foo   -      50      80    55       71     2         55,65      61,71
                g2        tx3  bar   -      3       20    3        15     1         3          17
                g7        tx7  baz   +      10      20    10       10     1         10         20
                """)  # noqa
        },
    })


@pytest.mark.parametrize("annotatable, effect, genes", [
    (Position("foo", 2), "intergenic", ""),
    (Position("foo", 7), "inter-coding_intronic", "g1"),
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
    ("foo", 10, 14, {"coding": {"g1"}}),
    ("foo", 28, 28, {"coding": {"g4", "g5"}}),
    ("foo", 41, 42, {"intergenic": set()}),
    ("foo", 26, 26, {"coding": {"g4"}, "peripheral": {"g5"}}),
    ("foo", 50, 50, {"intergenic": set()}),
    ("foo", 51, 51, {"peripheral": {"g6"}}),
    ("foo", 72, 72, {"peripheral": {"g6"}}),
    ("foo", 55, 55, {"peripheral": {"g6"}}),
    ("foo", 56, 56, {"coding": {"g6"}}),
    ("foo", 62, 62, {"inter-coding_intronic": {"g6"}}),
    ("foo", 65, 65, {"inter-coding_intronic": {"g6"}}),
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
        assert {
            c: {se.gene for se in effects}
            for c, effects in result.items()} == expected


def test_run_annotate_noncoding_effect(
    grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
            """),
        grr)

    with pipeline.open() as opened_pipeline:
        sea = opened_pipeline.annotators[0]
        assert isinstance(sea, SimpleEffectAnnotator)

        result = sea.run_annotate("baz", 12, 12)
        assert set(result) == {"noncoding"}
        noncoding_effects = result["noncoding"]
        assert {effect.gene for effect in noncoding_effects} == {"g7"}
        assert all(effect.effect_type == "noncoding"
                   for effect in noncoding_effects)


@pytest.mark.parametrize(
    "annotatable, worst_effect, worst_genes, genes,gene_effects", [
        (Position("foo", 2), "intergenic", "", "", ""),
        (Position("foo", 7), "inter-coding_intronic", "g1", "g1",
         "g1:inter-coding_intronic|g1:peripheral"),
        (Position("foo", 14), "coding", "g1", "g1", "g1:coding"),
        (Region("foo", 2, 14), "coding", "g1", "g1", "g1:coding"),
    ],
)
def test_full_annotation(
    annotatable: Annotatable,
    worst_effect: str,
    worst_genes: str,
    genes: str,
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
                - inter-coding_intronic_gene_list
                - inter-coding_intronic_genes
            """),
        grr)

    atts = pipeline.annotate(annotatable)
    assert atts["worst_effect"] == worst_effect
    assert atts["worst_effect_genes"] == worst_genes
    assert atts["genes"] == genes
    assert atts["gene_effects"] == gene_effects


def test_simple_effect_annotator_handles_none_annotatable(
    grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
            """),
        grr)

    result = pipeline.annotate(None)
    assert result == {
        "worst_effect": None,
        "worst_effect_genes": None,
    }


@pytest.fixture(scope="module")
def grr2() -> GenomicResourceProtocolRepo:
    return build_inmemory_test_repository({
        "gene_models": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: gene_models
                filename: gene_models.tsv
                format: "refflat"
            """),

            "gene_models.tsv": convert_to_tab_separated("""
                #geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds 
                g1        tx1  foo   +      2       92    12       82     2         12,52      42,82
                g1        tx2  foo   +      2       72    12       42     1         12         42
                """)  # noqa
        },
    })


@pytest.mark.parametrize(
    "annotatable,worst_effect,worst_genes,genes,gene_effects,effect_details", [
        (Region("foo", 13, 14),
         "coding", "g1", "g1", "g1:coding",
         "tx1_1:g1:coding|tx2_1:g1:coding"),
        (Region("foo", 53, 54),
         "coding", "g1", "g1", "g1:coding|g1:peripheral",
         "tx1_1:g1:coding|tx2_1:g1:peripheral"),
        (Region("foo", 45, 46),
         "inter-coding_intronic", "g1", "g1",
         "g1:inter-coding_intronic|g1:peripheral",
         "tx1_1:g1:inter-coding_intronic|tx2_1:g1:peripheral"),
    ],
)
def test_full_annotation2(
    annotatable: Annotatable,
    worst_effect: str,
    worst_genes: str,
    genes: str,
    gene_effects: str,
    effect_details: str,
    grr2: GenomicResourceRepo,
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
                - effect_details
                - coding_gene_list
                - coding_genes
                - peripheral_gene_list
                - peripheral_genes
                - inter-coding_intronic_gene_list
                - inter-coding_intronic_genes
            """),
        grr2)

    atts = pipeline.annotate(annotatable)
    assert atts["worst_effect"] == worst_effect
    assert atts["worst_effect_genes"] == worst_genes
    assert atts["genes"] == genes
    assert atts["gene_effects"] == gene_effects
    assert atts["effect_details"] == effect_details


def test_simple_effect_annotator_requires_gene_models_resource(
) -> None:
    empty_repo = build_inmemory_test_repository({})
    with pytest.raises(
        ValueError,
        match="gene model resource are missing in config and context",
    ):
        load_pipeline_from_yaml(
            textwrap.dedent("""
                - simple_effect_annotator: {}
                """),
            empty_repo,
        )
