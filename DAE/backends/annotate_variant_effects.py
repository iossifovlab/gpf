'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

from builtins import str
from builtins import next

from DAE import genomesDB
from variant_annotation.annotator import VariantAnnotator
from variant_annotation.variant import Variant

from .annotate_composite import AnnotatorBase
import itertools


GA = genomesDB.get_genome()  # @UndefinedVariable
gmDB = genomesDB.get_gene_models()  # @UndefinedVariable


class VcfVariantEffectsAnnotatorBase(AnnotatorBase):
    COLUMNS = [
        'effect_type',
        'effect_gene_genes',
        'effect_gene_types',
        'effect_details_transcript_ids',
        'effect_details_details',
    ]

    def __init__(self, genome=GA, gene_models=gmDB):
        self.variant_annotator = VariantAnnotator(
            reference_genome=genome,
            gene_models=gene_models,
        )
        assert self.variant_annotator is not None

    def annotate_variant_allele(self, allele):
        if allele['alternative'] is None:
            worst_effects = None
            gene_effects_genes = None
            gene_effects_types = None
            transcript_ids = None
            transcript_details = None
        else:
            effects = self.do_annotate_variant(
                chrom=allele['chrom'],
                position=allele['position'],
                ref=allele['reference'],
                alt=allele['alternative'])
            r = self.wrap_effects(effects)
            worst_effects = r[0]
            gene_effects_genes = r[1]
            gene_effects_types = r[2]
            transcript_ids = r[3]
            transcript_details = r[4]

        return worst_effects, \
            gene_effects_genes, \
            gene_effects_types, \
            transcript_ids, \
            transcript_details

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

    def __init__(self, genome=GA, gene_models=gmDB):
        super(VcfVariantEffectsAnnotator, self).__init__(
            genome, gene_models)

    def wrap_effects(self, effects):
        return self.effect_simplify(effects)

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
            return [[u'intergenic'], [u'intergenic']]
        if worst_effect == 'no-mutation':
            return [[u'no-mutation'], [u'no-mutation']]

        result = []
        for _severity, severity_effects in itertools.groupby(
                sorted_effects, cls.effect_severity):
            for gene, gene_effects in itertools.groupby(
                    severity_effects, lambda e: e.gene):
                result.append((gene, next(gene_effects).effect))

        return [
            [str(r[0]) for r in result],
            [str(r[1]) for r in result]
        ]

    @classmethod
    def transcript_effect(cls, effects):
        worst_effect = cls.worst_effect(effects)
        if worst_effect == 'intergenic':
            return ([u'intergenic'], [u'intergenic'])
        if worst_effect == 'no-mutation':
            return ([u'no-mutation'], [u'no-mutation'])

        result = {}
        for effect in effects:
            result[effect.transcript_id] = effect.create_effect_details()
        return (
            [str(r) for r in list(result.keys())],
            [str(r) for r in list(result.values())]
        )

    @classmethod
    def effect_simplify(cls, effects):
        if effects[0].effect == 'unk_chr':
            return (u'unk_chr',
                    [u'unk_chr'], [u'unk_chr'],
                    [u'unk_chr'], [u'unk_chr'])

        gene_effect = cls.gene_effect(effects)
        transcript_effect = cls.transcript_effect(effects)
        return (
            cls.worst_effect(effects),
            gene_effect[0], gene_effect[1],
            transcript_effect[0], transcript_effect[1]
        )
