# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.annotation.annotatable import Annotatable
from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AnnotationEffect
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome


@pytest.mark.parametrize(
    "variant_type,location,expected_effect_type,expected_effect_genes",
    [
        (
            Annotatable.Type.LARGE_DUPLICATION, "1:1590681-1628197",
            "CNV+", [("SLC35E2B", "CNV+"), ("CDK11B", "CNV+")],
        ),
        (
            Annotatable.Type.LARGE_DUPLICATION, "1:28298951-28369279",
            "CNV+", [("EYA3", "CNV+")],
        ),
        (
            Annotatable.Type.LARGE_DELETION, "1:40980559-40998902",
            "CNV-", [("EXO5", "CNV-"), ("ZNF684", "CNV-")],
        ),
        (
            Annotatable.Type.LARGE_DELETION, "1:63119256-63173918",
            "CNV-", [("DOCK7", "CNV-")],
        ),
    ],
)
def test_cnv_simple(
        gene_models_2019: GeneModels,
        genome_2019: ReferenceGenome,
        variant_type: Annotatable.Type,
        location: str, expected_effect_type: str,
        expected_effect_genes: list[tuple[str, str]]) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2019,
        genome_2019,
        location=location,
        variant_type=variant_type,
    )

    assert effects
    effect_type, effect_genes, _ = \
        AnnotationEffect.simplify_effects(effects)

    assert effect_type == expected_effect_type
    assert set(effect_genes) == set(expected_effect_genes)
