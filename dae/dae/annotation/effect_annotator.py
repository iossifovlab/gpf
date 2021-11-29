import copy
import logging

from box import Box

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AlleleEffects, AnnotationEffect

from .schema import Schema
from .annotatable import Annotatable, CNVAllele, VCFAllele

from .annotator_base import Annotator

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
        ]
    })

    def __init__(self, pipeline, config):
        super(EffectAnnotatorAdapter, self).__init__(pipeline, config)

        if self.config.get("genome") is None:
            self.genome = self.pipeline.context.get_reference_genome()
            if self.genome is None:
                logger.error(
                    "can't create effect annotator: config has no "
                    "reference genome specified and genome is missing "
                    "in the context")
                raise ValueError(
                    "can't create effect annotator: "
                    "genome is missing in config and context")
        else:
            genome_id = self.config.genome
            self.genome = self.pipeline.repository.get_resource(genome_id)

        if self.config.get("gene_models") is None:
            self.gene_models = self.pipeline.context.get_gene_models()
            if self.gene_models is None:
                raise ValueError(
                    "can't create effect annotator: "
                    "gene models are missing in config and context")
        else:
            self.gene_models = self.pipeline.repository.get_resource(
                self.config.gene_models)
            if self.gene_models is None:
                raise ValueError(
                    f"can't find gene models {self.config.gene_models} "
                    f"in the specified repository "
                    f"{self.pipeline.repository.repo_id}")

        self._annotation_schema = None
        self.attributes_list = copy.deepcopy(
            self.DEFAULT_ANNOTATION.attributes)
        if self.config.attributes:
            self.attributes_list = copy.deepcopy(self.config.attributes)

        self.gene_models.open()
        self.genome.open()
        promoter_len = self.config.get("promoter_len", 0)
        self.effect_annotator = EffectAnnotator(
            self.genome,
            self.gene_models,
            promoter_len=promoter_len
        )

    def _not_found(self, attributes):
        for attr in self.attributes_list:
            attributes[attr.destination] = ""

    @property
    def annotator_type(self):
        return "effect_annotator"

    @property
    def annotation_schema(self):
        if self._annotation_schema is None:
            schema = Schema()
            for attribute in self.get_annotation_config():
                prop_name = attribute.destination
                source_name = attribute.source

                source = self.EffectSource(
                    self.annotator_type, str(self.gene_models), source_name)
                schema.create_field(prop_name, "str", source)

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
