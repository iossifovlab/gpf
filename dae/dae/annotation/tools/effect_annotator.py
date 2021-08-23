#!/usr/bin/env python

import copy
import itertools

from box import Box

from dae.variants.attributes import VariantType

from dae.variant_annotation.annotator import \
    VariantAnnotator as EffectAnnotator
from dae.annotation.tools.annotator_base import Annotator


class VariantEffectAnnotator(Annotator):

    COLUMNS_SCHEMA = [
        ("effect_type", "str"),
        ("effect_gene_genes", "list(str)"),
        ("effect_gene_types", "list(str)"),
        ("effect_genes", "list(str)"),
        ("effect_details_transcript_ids", "list(str)"),
        ("effect_details_genes", "list(str)"),
        ("effect_details_details", "list(str)"),
        ("effect_details", "list(str)"),
    ]

    DEFAULT_ANNOTATION = Box({
        "attributes": [
            {
                "source": "effect_type",
                "dest": "effect_type"
            },

            {
                "source": "effect_genes",
                "dest": "effect_genes"
            },

            {
                "source": "effect_gene_genes",
                "dest": "effect_gene_genes"
            },

            {
                "source": "effect_gene_types",
                "dest": "effect_gene_types"
            },

            {
                "source": "effect_details",
                "dest": "effect_details"
            },

            {
                "source": "effect_details_transcript_ids",
                "dest": "effect_details_transcript_ids"
            },

            {
                "source": "effect_details_details",
                "dest": "effect_details_details"
            },
        ]
    })

    def __init__(self, gene_models, genome, **kwargs):
        super(VariantEffectAnnotator, self).__init__(gene_models, **kwargs)

        self.gene_models = gene_models
        self.genomic_sequence = genome

        promoter_len = kwargs.get("promoter_len", 0)
        self.effect_annotator = EffectAnnotator(
            self.genomic_sequence,
            self.gene_models,
            promoter_len=promoter_len
        )

        self.attributes_list = copy.deepcopy(
            self.DEFAULT_ANNOTATION.attributes)

        override = kwargs.get("override")
        if override:
            self.attributes_list = copy.deepcopy(override.attributes)

        self.gene_models.open()
        self.genomic_sequence.open()

    def _not_found(self, attributes):
        for attr in self.attributes_list:
            attributes[attr.dest] = ""

    def get_default_annotation(self):
        return copy.deepcopy(self.attributes_list)

    def _do_annotate(self, attributes, variant, _liftover_variants):
        if variant is None:
            self._not_found(attributes)
            return

        assert variant is not None
        length = None
        if VariantType.is_cnv(variant.variant_type):
            length = variant.end_position - variant.position

        effects = self.effect_annotator.do_annotate_variant(
            chrom=variant.chromosome,
            position=variant.position,
            ref=variant.reference,
            alt=variant.alternative,
            variant_type=variant.variant_type,
            length=length
        )

        r = self.wrap_effects(effects)

        result = {
            "effect_type": r[0],
            "effect_gene_genes": r[1],
            "effect_gene_types": r[2],
            "effect_genes": [f"{g}:{e}" for g, e in zip(r[1], r[2])],
            "effect_details_transcript_ids": r[3],
            "effect_details_genes": r[4],
            "effect_details_details": r[5],
            "effect_details": [
                f"{t}:{g}:{d}" for t, g, d in zip(r[3], r[4], r[5])],
        }

        attributes.update(result)

    def wrap_effects(self, effects):
        return self.effect_simplify(effects)

    @classmethod
    def effect_severity(cls, effect):
        return EffectAnnotator.Severity[effect.effect]

    @classmethod
    def sort_effects(cls, effects):
        sorted_effects = sorted(effects, key=lambda v: cls.effect_severity(v))
        return sorted_effects

    @classmethod
    def worst_effect(cls, effects):
        sorted_effects = cls.sort_effects(effects)
        return sorted_effects[0].effect

    @classmethod
    def gene_effect(cls, effects):
        sorted_effects = cls.sort_effects(effects)
        worst_effect = sorted_effects[0].effect
        if worst_effect == "intergenic":
            return [["intergenic"], ["intergenic"]]
        if worst_effect == "no-mutation":
            return [["no-mutation"], ["no-mutation"]]

        result = []
        for _severity, severity_effects in itertools.groupby(
            sorted_effects, cls.effect_severity
        ):
            for gene, gene_effects in itertools.groupby(
                severity_effects, lambda e: e.gene
            ):
                result.append((gene, next(gene_effects).effect))

        return [[str(r[0]) for r in result], [str(r[1]) for r in result]]

    @classmethod
    def transcript_effect(cls, effects):
        worst_effect = cls.worst_effect(effects)
        if worst_effect == "intergenic":
            return (
                ["intergenic"],
                ["intergenic"],
                ["intergenic"],
                ["intergenic"],
            )
        if worst_effect == "no-mutation":
            return (
                ["no-mutation"],
                ["no-mutation"],
                ["no-mutation"],
                ["no-mutation"],
            )

        transcripts = []
        genes = []
        details = []
        for effect in effects:
            transcripts.append(effect.transcript_id)
            genes.append(effect.gene)
            details.append(effect.create_effect_details())

        return (transcripts, genes, details)

    @classmethod
    def effect_simplify(cls, effects):
        if effects[0].effect == "unk_chr":
            return (
                "unk_chr",
                ["unk_chr"],
                ["unk_chr"],
                ["unk_chr"],
                ["unk_chr"],
            )

        gene_effect = cls.gene_effect(effects)
        transcript_effect = cls.transcript_effect(effects)
        return (
            cls.worst_effect(effects),
            gene_effect[0],
            gene_effect[1],
            transcript_effect[0],
            transcript_effect[1],
            transcript_effect[2],
        )
