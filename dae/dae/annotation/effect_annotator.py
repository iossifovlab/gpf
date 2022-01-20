import copy
import logging

from typing import Dict, List

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AlleleEffects, AnnotationEffect
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.gene_models import \
    load_gene_models_from_resource

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
        resource = pipeline.repository.get_resource(genome_id)
        genome = open_reference_genome_from_resource(resource)

    if config.get("gene_models") is None:
        gene_models = pipeline.context.get_gene_models()
        if gene_models is None:
            raise ValueError(
                "can't create effect annotator: "
                "gene models are missing in config and context")
    else:
        gene_models_id = config.get("gene_models")
        resource = pipeline.repository.get_resource(gene_models_id)
        gene_models = load_gene_models_from_resource(resource)

    return EffectAnnotatorAdapter(config, genome, gene_models)


class EffectAnnotatorAdapter(Annotator):

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

    # FIXME
    def _not_found(self, attributes):
        for attr in self.attributes_list:
            attributes[attr.destination] = ""

    def get_all_annotation_attributes(self) -> List[Dict]:
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

    def _do_annotate(
            self, annotatable: Annotatable, _context: Dict):

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

        # r = AnnotationEffect.wrap_effects(effects)
        full_desc = AnnotationEffect.effects_description(effects)
        result = {
            "worst_effect": full_desc[0],
            "gene_effects": full_desc[1],
            "effect_details": full_desc[2],
            "allele_effects": AlleleEffects.from_effects(effects),
        }

        return result
