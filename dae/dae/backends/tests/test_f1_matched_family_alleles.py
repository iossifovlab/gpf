"""
Created on Jul 18, 2018

@author: lubo
"""
import pytest

from dae.utils.regions import Region

from dae.effect_annotation.effect import EffectGene


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "position,inheritance,effect_types,return_reference,matched_alleles",
    [
        (878152, None, None, True, [0, 1, 2]),
        (878152, None, None, False, [1, 2]),
        (878152, "denovo", ["missense"], True, [2]),
        (878152, "mendelian", ["synonymous"], True, [1]),
        (878152, "mendelian", None, True, [0, 1]),
        (878152, "mendelian", None, False, [1]),
    ],
)
def test_f1_matched_alleles(
    variants_impl,
    variants,
    position,
    inheritance,
    effect_types,
    return_reference,
    matched_alleles,
):

    vvars = variants_impl(variants)("backends/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=[Region("1", position, position)],
        inheritance=inheritance,
        effect_types=effect_types,
        return_reference=return_reference,
        return_unknown=True,
    )
    vs = list(vs)
    assert len(vs) == 1

    v = vs[0]
    print(v, v.effects, v.matched_alleles)
    print(v.matched_alleles_indexes, "==", matched_alleles)
    assert v.matched_alleles_indexes == matched_alleles


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "position,inheritance,effect_types,return_reference,"
    "matched_alleles_effects",
    [
        (878152, None, None, True, [(0, []), (1, []), (2, [])]),
        (878152, None, None, True, [(0, []), (1, []), (2, [])]),
        (
            878152,
            "denovo",
            ["missense"],
            True,
            [(2, [EffectGene("SAMD11", "missense")])],
        ),
        (
            878152,
            "mendelian",
            ["synonymous"],
            True,
            [(1, [EffectGene("SAMD11", "synonymous")])],
        ),
        (878152, "mendelian", None, True, [(0, []), (1, [])]),
        (878152, "mendelian", None, True, [(0, []), (1, [])]),
        (
            878152,
            None,
            ["missense", "synonymous"],
            True,
            [
                (1, [EffectGene("SAMD11", "synonymous")]),
                (2, [EffectGene("SAMD11", "missense")]),
            ],
        ),
    ],
)
def test_f1_requested_effects(
    variants_impl,
    variants,
    position,
    inheritance,
    effect_types,
    return_reference,
    matched_alleles_effects,
):

    vvars = variants_impl(variants)("backends/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=[Region("1", position, position)],
        inheritance=inheritance,
        effect_types=effect_types,
        return_reference=return_reference,
        return_unknown=True,
    )
    vs = list(vs)
    assert len(vs) == 1

    v = vs[0]

    print(v, v.effects, v.matched_alleles)
    assert len(v.matched_alleles) == len(matched_alleles_effects)

    # print(v.matched_gene_effects)

    # for matched_allele, (allele_index, matched_effects) in \
    #         zip(v.matched_alleles, matched_alleles_effects):
    #     assert matched_allele.allele_index == allele_index
    #     assert matched_allele.matched_gene_effects == matched_effects
