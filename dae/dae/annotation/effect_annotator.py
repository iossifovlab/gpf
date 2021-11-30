import copy
import logging

from typing import Dict, List
from box import Box

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AlleleEffects, AnnotationEffect

from .schema import Schema
from .annotatable import Annotatable, CNVAllele, VCFAllele

from .annotator_base import Annotator, ATTRIBUTES_SCHEMA

logger = logging.getLogger(__name__)


class EffectAnnotatorAdapter(Annotator):

    class EffectSource(Schema.Source):
        def __init__(
                self, annotator_type: str, resource_id: str,
                effect_attribute: str):
            super().__init__(annotator_type, resource_id)
            self.effect_attribute = effect_attribute

        def __repr__(self):
            repr = [super().__repr__(), self.effect_attribute]
            return "; ".join(repr)

    DEFAULT_ANNOTATION = Box({
        "attributes": [
            {
                "source": "effect_type",
                "destination": "effect_type"
            },

            {
                "source": "effect_genes",
                "destination": "effect_genes"
            },

            {
                "source": "effect_details",
                "destination": "effect_details"
            },

            {
                "source": "allele_effects",
                "destination": "allele_effects",
                "internal": True,
            }
        ]
    })

    def __init__(self, config, genome, gene_models):
        super(EffectAnnotatorAdapter, self).__init__(config)

        self.genome = genome
        self.gene_models = gene_models

        self.gene_models.open()
        self.genome.open()

        self._annotation_schema = None
        self.attributes_list = [
            attr
            for attr in self.DEFAULT_ANNOTATION.attributes
        ]
        if self.config.get("attributes"):
            self.attributes_list = copy.deepcopy(self.config.get("attributes"))

        promoter_len = self.config.get("promoter_len", 0)
        self.effect_annotator = EffectAnnotator(
            self.genome,
            self.gene_models,
            promoter_len=promoter_len
        )

    def _not_found(self, attributes):
        for attr in self.attributes_list:
            attributes[attr.destination] = ""

    def get_all_annotation_attributes(self) -> List[Dict]:
        result = [
            {
                "source": "effect_type",
                "type": "str",
                "desc": "worst effect",
            },
            {
                "source": "effect_gene_genes",
                "type": "object",
                "desc": ""
            },
            {
                "source": "effect_gene_types",
                "type": "object",
                "desc": ""
            },
            {
                "source": "effect_genes",
                "type": "str",
                "desc": ""
            },
            {
                "source": "effect_details_transcript_ids",
                "type": "object",
                "desc": ""
            },
            {
                "source": "effect_details_genes",
                "type": "object",
                "desc": ""
            },
            {
                "source": "effect_details_details",
                "type": "object",
                "desc": ""
            },
            {
                "source": "effect_details",
                "type": "str",
                "desc": ""
            },
            {
                "source": "allele_effects",
                "type": "object",
                "desc": ""
            },
        ]
        return result

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["effect_annotator"]
            },
            "id": {
                "type": "string",
                "required": False,
            },
            "gene_models": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "genome": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "attributes": {
                "type": "list",
                "nullable": True,
                "default": None,
                "schema": ATTRIBUTES_SCHEMA
            }
        }

        validator = cls.ConfigValidator(schema)
        validator.allow_unknown = True

        logger.debug(f"validating effect annotator config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for effect annotator: "
                f"{validator.errors}")
            raise ValueError(
                f"wrong effect annotator config {validator.errors}")
        return validator.document

    @staticmethod
    def annotator_type():
        return "effect_annotator"

    @property
    def annotation_schema(self):
        if self._annotation_schema is None:
            schema = Schema()
            for attribute in self.get_annotation_config():
                if attribute.get("internal"):
                    continue

                dest_name = attribute.destination
                source_name = attribute.source

                source = self.EffectSource(
                    self.annotator_type, str(self.gene_models), source_name)
                schema.create_field(dest_name, "str", source)

            self._annotation_schema = schema
        return self._annotation_schema

    def get_annotation_config(self):
        return copy.deepcopy(self.attributes_list)

    def _do_annotate(
            self, attributes, annotatable: Annotatable, _liftover_context):

        if annotatable is None:
            self._not_found(attributes)
            return

        if not isinstance(annotatable, VCFAllele) and  \
                not isinstance(annotatable, CNVAllele):
            self._not_found(attributes)
            return

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
            "allele_effects": AlleleEffects.from_effects(effects),
        }

        attributes.update(result)
