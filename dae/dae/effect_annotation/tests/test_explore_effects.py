from dae.effect_annotation.annotator import (
    VariantAnnotator as VariantAnnotation,
)


def test_chr1_95712170_del_var(genomic_sequence_2013, gene_models_2013):
    effects = VariantAnnotation.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:95712170", var="del(3)"
    )

    assert len(effects) == 7

    simplified_effects = VariantAnnotation.effect_simplify(effects)
    print(simplified_effects)

    description = VariantAnnotation.effect_description(effects)
    print(description)
