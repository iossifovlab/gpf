"""Defines variant effect annotator."""

import copy
import logging

from typing import cast, Optional

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AlleleEffects, AnnotationEffect
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource
from dae.genomic_resources.gene_models import GeneModels

from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.gene_models import \
    build_gene_models_from_resource

from .annotatable import Annotatable, CNVAllele, VCFAllele

from .annotator_base import Annotator, ATTRIBUTES_SCHEMA

logger = logging.getLogger(__name__)


def build_effect_annotator(pipeline, config):
    """Build a variant effect annotator based on pipeline and configuration."""
    config = EffectAnnotatorAdapter.validate_config(config)

    if config.get("annotator_type") != "effect_annotator":
        logger.error(
            "wrong usage of build_effect_annotator with an "
            "annotator config: %s", config)
        raise ValueError(f"wrong annotator type: {config}")

    if config.get("genome") is None:
        genome = get_genomic_context().get_reference_genome()
        if genome is None:
            logger.error(
                "can't create effect annotator: config has no "
                "reference genome specified and genome is missing "
                "in the context")
            raise ValueError(
                "can't create effect annotator: "
                "genome is missing in config and context")
    else:
        genome_id = config.get("genome")
        resource = pipeline.repository.get_resource(genome_id)
        genome = build_reference_genome_from_resource(resource)

    if config.get("gene_models") is None:
        gene_models = get_genomic_context().get_gene_models()
        if gene_models is None:
            raise ValueError(
                "can't create effect annotator: "
                "gene models are missing in config and context")
    else:
        gene_models_id = config.get("gene_models")
        resource = pipeline.repository.get_resource(gene_models_id)
        gene_models = build_gene_models_from_resource(resource).load()

    return EffectAnnotatorAdapter(config, genome, gene_models)


class EffectAnnotatorAdapter(Annotator):
    """Defines variant effect annotator."""

    DEFAULT_ANNOTATION = {
        "attributes": [
            {
                "source": "worst_effect",
                "destination": "worst_effect"
            },

            {
                "source": "gene_effects",
                "destination": "gene_effects"
            },

            {
                "source": "effect_details",
                "destination": "effect_details"
            },
        ]
    }

    def __init__(
            self, config, genome: ReferenceGenome, gene_models: GeneModels):
        super().__init__(config)

        assert isinstance(genome, ReferenceGenome)
        assert isinstance(gene_models, GeneModels)

        self.genome = genome
        self.gene_models = gene_models

        self._annotation_schema = None
        self._annotation_config: Optional[list[dict[str, str]]] = None

        promoter_len = self.config.get("promoter_len", 0)
        self.effect_annotator = EffectAnnotator(
            self.genome,
            self.gene_models,
            promoter_len=promoter_len
        )

    def close(self):
        self.genome.close()

    def open(self):  # FIXME:
        self.genome.open()
        self.gene_models.load()

        return self

    def is_open(self):  # FIXME:
        return self.genome.is_open()

    def _not_found(self, attributes):
        for attr in self.get_annotation_config():
            attributes[attr["destination"]] = ""

    def get_all_annotation_attributes(self) -> list[dict]:
        result = [
            {
                "name": "worst_effect",
                "type": "str",
                "desc": "Worst effect accross all transcripts.",
            },
            {
                "name": "gene_effects",
                "type": "str",
                "desc": "Effects types for genes. "
                        "Format: <gene_1>:<effect_1>|... "
                "A gene can be repeated."
            },
            {
                "name": "effect_details",
                "type": "str",
                "desc": "Effect details for each affected transcript. "
                "Format: <transcript 1>:<gene 1>:<effect 1>:<details 1>|..."
            },
            {
                "name": "allele_effects",
                "type": "object",
                "desc": "The a list of a python objects with details of the "
                        "effects for each affected transcript. "
            },
            {
                "name": "gene_list",
                "type": "object",
                "desc": "List of all genes"
            },
            {
                "name": "LGD_gene_list",
                "type": "object",
                "desc": "List of all LGD genes"
            },
        ]
        return result

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["effect_annotator"]
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

        logger.debug("validating effect annotator config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for effect annotator: %s",
                validator.errors)
            raise ValueError(
                f"wrong effect annotator config {validator.errors}")
        return cast(dict, validator.document)

    def annotator_type(self) -> str:
        return "effect_annotator"

    def get_annotation_config(self):
        if self._annotation_config is None:
            if self.config.get("attributes"):
                self._annotation_config = copy.deepcopy(
                    self.config.get("attributes"))
            else:
                self._annotation_config = copy.deepcopy(
                    self.DEFAULT_ANNOTATION["attributes"])
        return self._annotation_config

    @property
    def resources(self):
        return {
            self.gene_models.resource_id,
            self.genome.resource_id
        }

    def _do_annotate(
            self, annotatable: Annotatable, _context: dict):

        result: dict = {}
        if annotatable is None:
            self._not_found(result)
            return result

        if not isinstance(annotatable, VCFAllele) and  \
                not isinstance(annotatable, CNVAllele):
            self._not_found(result)
            return result

        length = len(annotatable)

        effects = self.effect_annotator.do_annotate_variant(
            chrom=annotatable.chromosome,
            pos=annotatable.position,
            ref=annotatable.reference,
            alt=annotatable.alternative,
            variant_type=annotatable.type,
            length=length
        )

        gene_list = list(set(
            AnnotationEffect.gene_effects(effects)[0]
        ))
        lgd_gene_list = list(set(
            AnnotationEffect.lgd_gene_effects(effects)[0]
        ))
        # r = AnnotationEffect.wrap_effects(effects)
        full_desc = AnnotationEffect.effects_description(effects)
        result = {
            "worst_effect": full_desc[0],
            "gene_effects": full_desc[1],
            "effect_details": full_desc[2],
            "allele_effects": AlleleEffects.from_effects(effects),
            "gene_list": gene_list,
            "lgd_gene_list": lgd_gene_list
        }

        return self._remap_annotation_attributes(result)
