#!/usr/bin/env python

import copy

import pyarrow as pa

from box import Box

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AnnotationEffect

from .schema import Schema
from .annotatable import Annotatable, CNVAllele, VCFAllele

from .annotator_base import Annotator


class EffectAnnotatorAdapter(Annotator):

    SCHEMA = {
        "effect_type": (str, pa.string()),
        "effect_gene_genes": (list, pa.list_(pa.string())),
        "effect_gene_types": (list, pa.list_(pa.string())),
        "effect_genes": (list, pa.list_(pa.string())),
        "effect_details_transcript_ids": (list, pa.list_(pa.string())),
        "effect_details_genes": (list, pa.list_(pa.string())),
        "effect_details_details": (list, pa.list_(pa.string())),
        "effect_details": (list, pa.list_(pa.string())),
    }

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
        super(EffectAnnotatorAdapter, self).__init__(gene_models, **kwargs)

        self.gene_models = gene_models
        self.genomic_sequence = genome

        self._annotation_schema = None
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

    @property
    def annotator_type(self):
        return "effect_annotator"

    @property
    def annotation_schema(self):
        if self._annotation_schema is None:
            schema = Schema()
            for attribute in self.get_annotation_config():
                prop_name = attribute.dest
                py_type, pa_type = self.SCHEMA[attribute.source]
                schema.create_field(
                    prop_name, py_type, pa_type,
                    self.annotator_type,
                    f"{self.genomic_sequence.resource_id}:"
                    f"{self.gene_models.resource_id}",
                    attribute.source)
            self._annotation_schema = schema
        return self._annotation_schema

    def get_annotation_config(self):
        return copy.deepcopy(self.attributes_list)

    def _do_annotate(
            self, attributes, annotatable: Annotatable, _liftover_context):

        assert isinstance(annotatable, VCFAllele) or \
            isinstance(annotatable, CNVAllele), annotatable

        print(annotatable)

        if annotatable is None:
            self._not_found(attributes)
            return

        assert annotatable is not None
        length = len(annotatable)

        effects = self.effect_annotator.do_annotate_variant(
            chrom=annotatable.chromosome,
            position=annotatable.position,
            ref=annotatable.reference,
            alt=annotatable.alternative,
            variant_type=annotatable.type,
            length=length
        )

        r = AnnotationEffect.wrap_effects(effects)

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

