'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function

from DAE import genomesDB
import numpy as np
from variant_annotation.annotator import VariantAnnotator
from variant_annotation.variant import Variant
from variants.annotate_composite import AnnotatorBase
import itertools


GA = genomesDB.get_genome()  # @UndefinedVariable
gmDB = genomesDB.get_gene_models()  # @UndefinedVariable


class VcfVariantEffectsAnnotatorBase(AnnotatorBase):
    COLUMNS = ['effectType', 'effectGene', 'effectDetails']

    def __init__(self, genome=GA, gene_models=gmDB):
        self.variant_annotator = VariantAnnotator(
            reference_genome=genome,
            gene_models=gene_models,
        )
        assert self.variant_annotator is not None

    def annotate_variant(self, vcf_variant):
        result = []
        for alt in vcf_variant.ALT:
            variant = Variant(
                chrom=vcf_variant.CHROM,
                position=vcf_variant.start + 1,
                ref=vcf_variant.REF,
                alt=alt)
            effects = self.variant_annotator.annotate(variant)
            effects = self.do_annotate_variant(
                chrom=vcf_variant.CHROM,
                position=vcf_variant.start + 1,
                ref=vcf_variant.REF,
                alt=alt)
            result.append(self.wrap_effects(effects))
        result = np.array(result)
        return result[:, 0], result[:, 1], result[:, 2]

    def wrap_effects(self, effects):
        raise NotImplementedError()

    def do_annotate_variant(self, chrom, position, ref, alt):
        variant = Variant(
            chrom=chrom,
            position=position,
            ref=ref,
            alt=alt)
        effects = self.variant_annotator.annotate(variant)
        return effects


class VcfVariantEffectsAnnotator(VcfVariantEffectsAnnotatorBase):
    COLUMNS = ['effectType', 'effectGene', 'effectDetails']

    def __init__(self, genome=GA, gene_models=gmDB):
        super(VcfVariantEffectsAnnotator, self).__init__(
            genome, gene_models)

    def wrap_effects(self, effects):
        effect_type, effect_gene, _ = \
            self.effect_simplify(effects)
        return (effect_type, np.array(effect_gene), effects)

    @classmethod
    def effect_severity(cls, effect):
        return - VariantAnnotator.Severity[effect.effect]

    @classmethod
    def sort_effects(cls, effects):
        sorted_effects = sorted(
            effects,
            key=lambda v: cls.effect_severity(v))
        return sorted_effects

    @classmethod
    def worst_effect(cls, effects):
        sorted_effects = cls.sort_effects(effects)
        return sorted_effects[0].effect

    @classmethod
    def gene_effect(cls, effects):
        sorted_effects = cls.sort_effects(effects)
        worst_effect = sorted_effects[0].effect
        if worst_effect == 'intergenic':
            return [('intergenic', 'intergenic')]
        if worst_effect == 'no-mutation':
            return [('no-mutation', 'no-mutation')]

        result = []
        for _severity, severity_effects in itertools.groupby(
                sorted_effects, cls.effect_severity):
            for gene, gene_effects in itertools.groupby(
                    severity_effects, lambda e: e.gene):
                result.append((gene, next(gene_effects).effect))
        return result

    @classmethod
    def transcript_effect(cls, effects):
        worst_effect = cls.worst_effect(effects)
        if worst_effect == 'intergenic':
            return [('intergenic', 'intergenic')]
        if worst_effect == 'no-mutation':
            return [('no-mutation', 'no-mutation')]

        result = {}
        for effect in effects:
            result[effect.transcript_id] = effect.create_effect_details()
        return list(result.items())

    @classmethod
    def effect_simplify(cls, effects):
        if effects[0].effect == 'unk_chr':
            return ('unk_chr', ('unk_chr', 'unk_chr'), ('unk_chr', 'unk_chr'))

        return (
            cls.worst_effect(effects),
            cls.gene_effect(effects),
            cls.transcript_effect(effects)
        )
