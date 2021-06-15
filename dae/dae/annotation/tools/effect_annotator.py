#!/usr/bin/env python

import itertools
from typing import List, Tuple

from collections import OrderedDict

from dae.variants.attributes import VariantType

from dae.variant_annotation.annotator import VariantAnnotator
from dae.annotation.tools.annotator_base import Annotator


class EffectAnnotatorBase(Annotator):
    COLUMNS_SCHEMA: List[Tuple[str, str]] = []

    def __init__(self, config, genomes_db, **kwargs):
        super(EffectAnnotatorBase, self).__init__(config, genomes_db)

        self.effect_annotator = VariantAnnotator(
            self.genomic_sequence,
            self.gene_models,
            promoter_len=self.config.options.prom_len,
        )

        self.columns = OrderedDict()
        for col_name, _col_type in self.COLUMNS_SCHEMA:
            self.columns[col_name] = getattr(self.config.columns, col_name)

    def collect_annotator_schema(self, schema):
        super(EffectAnnotatorBase, self).collect_annotator_schema(schema)
        for col_name, col_type in self.COLUMNS_SCHEMA:
            if self.columns.get(col_name, None):
                schema.create_column(self.columns[col_name], col_type)

    def _not_found(self, aline):
        for _col_name, col_conf in self.columns.items():
            if col_conf:
                aline[col_conf] = ""

    def do_annotate(self, aline, variant, liftover_variants):
        raise NotImplementedError()


class VariantEffectAnnotator(EffectAnnotatorBase):

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

    def __init__(self, config, genomes_db, **kwargs):
        super(VariantEffectAnnotator, self).__init__(
            config, genomes_db, **kwargs
        )

    def do_annotate(self, aline, variant, liftover_variants):
        if variant is None:
            self._not_found(aline)
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

        aline[self.columns["effect_type"]] = r[0]

        aline[self.columns["effect_gene_genes"]] = r[1]
        aline[self.columns["effect_gene_types"]] = r[2]
        aline[self.columns["effect_genes"]] = [
            "{}:{}".format(g, e) for g, e in zip(r[1], r[2])
        ]
        aline[self.columns["effect_details_transcript_ids"]] = r[3]
        aline[self.columns["effect_details_genes"]] = r[4]
        aline[self.columns["effect_details_details"]] = r[5]
        aline[self.columns["effect_details"]] = [
            "{}:{}:{}".format(t, g, d) for t, g, d in zip(r[3], r[4], r[5])
        ]

    def wrap_effects(self, effects):
        return self.effect_simplify(effects)

    @classmethod
    def effect_severity(cls, effect):
        return -VariantAnnotator.Severity[effect.effect]

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
