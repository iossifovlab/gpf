# pylint: disable=W0621,C0114,C0116,W0212,W0613,R0917

import pytest
from dae.annotation.annotatable import Annotatable
from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AnnotationEffect
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.testing.t4c8_import import t4c8_genes as setup_t4c8_genes
from dae.testing.t4c8_import import t4c8_genome as setup_t4c8_genome


@pytest.fixture(scope="session")
def t4c8_genome(tmp_path_factory: pytest.TempPathFactory) -> ReferenceGenome:
    root_path = tmp_path_factory.mktemp("t4c8_genome")
    genome = setup_t4c8_genome(root_path)
    genome.open()
    return genome


@pytest.fixture(scope="session")
def t4c8_genes(tmp_path_factory: pytest.TempPathFactory) -> GeneModels:
    root_path = tmp_path_factory.mktemp("t4c8_genes")
    gene_models = setup_t4c8_genes(root_path)
    gene_models.load()
    return gene_models


@pytest.mark.parametrize(
    "variant_type,location,"
    "expected_effect_type,expected_effect_genes,expected_effect_details",
    [
        (
            Annotatable.Type.LARGE_DUPLICATION, "chr1:93-95",
            "CNV+", [("intergenic", "CNV+")],
            [("intergenic", "intergenic", "CNV+", "3")],
        ),
        (
            Annotatable.Type.LARGE_DUPLICATION, "chr1:1-91",
            "CNV+", [("t4", "CNV+")],
            [("tx1", "t4", "CNV+", "91")],
        ),
        (
            Annotatable.Type.LARGE_DELETION, "chr1:1-150",
            "CNV-", [("t4", "CNV-"), ("c8", "CNV-")],
            [("tx1", "t4", "CNV-", "150"),
             ("tx1", "c8", "CNV-", "150")],
        ),

    ],
)
def test_cnv_annotation(
    t4c8_genome: ReferenceGenome,
    t4c8_genes: GeneModels,
    variant_type: Annotatable.Type,
    location: str, expected_effect_type: str,
    expected_effect_genes: list[tuple[str, str]],
    expected_effect_details: list[tuple[str, str, str, str]],
) -> None:
    effects = EffectAnnotator.annotate_variant(
        t4c8_genes,
        t4c8_genome,
        location=location,
        variant_type=variant_type,
    )

    assert effects
    effect_type, effect_genes, effect_details = \
        AnnotationEffect.simplify_effects(effects)

    assert effect_type == expected_effect_type
    assert effect_genes == expected_effect_genes
    assert effect_details == expected_effect_details
