import copy
import logging

from typing import Dict, List
from box import Box

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AlleleEffects, AnnotationEffect
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.gene_models import GeneModels

from .schema import Schema
from .annotatable import Annotatable, CNVAllele, VCFAllele

from .annotator_base import Annotator, ATTRIBUTES_SCHEMA

logger = logging.getLogger(__name__)


def build_effect_annotator(pipeline, config):
    config = EffectAnnotatorAdapter.validate_config(config)

    if config.get("annotator_type") != "effect_annotator":
        logger.error(
            f"wrong usage of build_effect_annotator with an "
            f"annotator config: {config}")
        raise ValueError(f"wrong annotator type: {config}")

    if config.get("genome") is None:
        genome = pipeline.context.get_reference_genome()
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
        genome = pipeline.repository.get_resource(genome_id)
        if genome is None:
            logger.error(
                f"can't find reference genome {genome_id} in genomic "
                f"resources repository {pipeline.repository.repo_id}")
            raise ValueError(f"can't find genome {genome_id}")

    if config.get("gene_models") is None:
        gene_models = pipeline.context.get_gene_models()
        if gene_models is None:
            raise ValueError(
                "can't create effect annotator: "
                "gene models are missing in config and context")
    else:
        gene_models_id = config.get("gene_models")
        gene_models = pipeline.repository.get_resource(gene_models_id)
        if gene_models is None:
            raise ValueError(
                f"can't find gene models {gene_models_id} "
                f"in the specified repository "
                f"{pipeline.repository.repo_id}")

    return EffectAnnotatorAdapter(config, genome.open(), gene_models.open())


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

    def __init__(
            self, config, genome: ReferenceGenome, gene_models: GeneModels):
        super(EffectAnnotatorAdapter, self).__init__(config)

        assert isinstance(genome, ReferenceGenome)
        assert isinstance(gene_models, GeneModels)

        self.genome = genome
        self.gene_models = gene_models

        self._annotation_schema = None
        self._annotation_config = None

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

                dest_name = attribute.destination
                source_name = attribute.source

                source = self.EffectSource(
                    self.annotator_type, str(self.gene_models), source_name)
                schema.create_field(
                    dest_name, "str",
                    attribute.get("internal", False),
                    source)

            self._annotation_schema = schema
        return self._annotation_schema

    def get_annotation_config(self):
        if self._annotation_config is None:
            if self.config.get("attributes"):
                self._annotation_config = copy.deepcopy(
                    self.config.get("attributes"))
            else:
                self._annotation_config = copy.deepcopy(
                    self.DEFAULT_ANNOTATION.attributes)
        return self._annotation_config

    def _do_annotate(
            self, annotatable: Annotatable, _context: Dict):

        result = {}
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

        return result
