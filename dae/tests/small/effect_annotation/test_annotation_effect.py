# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.effect_annotation.effect import AnnotationEffect


@pytest.mark.parametrize(
    "effect_types, filter_effect, expected_genes", [
        (["nonsense", "frame-shift"], "frame-shift", ["gene2"]),
        (["nonsense", "frame-shift"], "LGDs", ["gene1", "gene2"]),
    ],
)
def test_annotation_effect_filter_genes(
    effect_types: list[str],
    filter_effect: str,
    expected_genes: list[str],
) -> None:
    effects = [
        AnnotationEffect(effect_type)
        for effect_type in effect_types
    ]

    for idx, eff in enumerate(effects, start=1):
        eff.gene = f"gene{idx}"

    genes = AnnotationEffect.filter_genes(effects, filter_effect)
    assert set(genes) == set(expected_genes)


@pytest.mark.parametrize(
    "effect_types, filter_effect, expected_genes, expected_types", [
        (["nonsense", "frame-shift"], "frame-shift",
         ["gene2"], ["frame-shift"]),
        (["nonsense", "frame-shift"], "LGDs",
         ["gene1", "gene2"], ["nonsense", "frame-shift"]),
    ],
)
def test_annotation_effect_filter_gene_effects(
    effect_types: list[str],
    filter_effect: str,
    expected_genes: list[str],
    expected_types: list[str],
) -> None:
    effects = [
        AnnotationEffect(effect_type)
        for effect_type in effect_types
    ]

    for idx, eff in enumerate(effects, start=1):
        eff.gene = f"gene{idx}"

    gene_effects = AnnotationEffect.filter_gene_effects(effects, filter_effect)
    assert set(gene_effects[0]) == set(expected_genes)
    assert set(gene_effects[1]) == set(expected_types)
