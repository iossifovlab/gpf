import pytest

from dae.annotation.annotatable import Annotatable

from dae.variant_annotation.annotator import VariantAnnotator


@pytest.mark.parametrize(
    "variant_type,location,effect_type,effect_genes",
    [
        (
            Annotatable.Type.large_duplication, "1:1590681-1628197",
            "CNV+", [('SLC35E2B', 'CNV+'), ('CDK11B', 'CNV+')]
        ),
        (
            Annotatable.Type.large_duplication, "1:28298951-28369279",
            "CNV+", [("EYA3", "CNV+")]
        ),
        (
            Annotatable.Type.large_deletion, "1:40980559-40998902",
            "CNV-", [("EXO5", "CNV-"), ("ZNF684", "CNV-")]
        ),
        (
            Annotatable.Type.large_deletion, "1:63119256-63173918",
            "CNV-", [("DOCK7", "CNV-")]
        ),
    ],
)
def test_cnv_simple(
        genomic_sequence_2013, gene_models_2013,
        variant_type, location, effect_type, effect_genes):
    effects = VariantAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc=location,
        variant_type=variant_type
    )
    assert effects
    et, eg, _ = \
        VariantAnnotator.effect_simplify(effects)

    assert et == effect_type
    assert set(eg) == set(effect_genes)
