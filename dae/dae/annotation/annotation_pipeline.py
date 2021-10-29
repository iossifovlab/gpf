#!/usr/bin/env python
import logging
from itertools import chain
from typing import List, Optional

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.variants.core import Allele
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.annotation.tools.annotator_base import Annotator
from dae.annotation.tools.schema import Schema
from dae.annotation.tools.utils import AnnotatorFactory


logger = logging.getLogger(__name__)


DEFAULT_ANNOTATION_SCHEMA = {
    "attributes": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "source": {"type": "string"},
                "dest": {"type": "string"},
                "position_aggregator": {"type": "string"},
                "nucleotide_aggregator": {"type": "string"},
            }
        }
    }
}


ANNOTATOR_SCHEMA = {
    "type": "dict",
    "schema": {
        "annotator": {"type": "string", "required": True},
        "resource": {"type": "string"},
        "gene_models": {"type": "string"},
        "chain": {"type": "string"},
        "genome": {"type": "string"},
        "target_genome": {"type": "string"},
        "liftover": {"type": "string"},
        "override": {"type": "dict", "schema": DEFAULT_ANNOTATION_SCHEMA}
    }
}


ANNOTATION_PIPELINE_SCHEMA = {
    "effect_annotators": {
        "type": "list",
        "schema": ANNOTATOR_SCHEMA,
    },
    "liftover_annotators": {
        "type": "list",
        "schema": ANNOTATOR_SCHEMA,
    },
    "score_annotators": {
        "type": "list",
        "schema": ANNOTATOR_SCHEMA,
    }
}


class AnnotationPipeline():
    def __init__(self, config, repository):
        self.annotators: List[Annotator] = []
        self.config: dict = config
        self.repository: GenomicResourceRepo = repository
        self._annotation_schema = None

    @staticmethod
    def load_and_parse(config_path: str) -> dict:
        with open(config_path, "r") as infile:
            content = infile.read()
        return AnnotationPipeline.parse_config(content)

    @staticmethod
    def parse_config(content: str) -> dict:
        config = GPFConfigParser.parse_and_interpolate(content)
        pipeline_config = GPFConfigParser.process_config(
            config, ANNOTATION_PIPELINE_SCHEMA
        )
        return pipeline_config

    @staticmethod
    def build(
            pipeline_config: dict,
            repository: GenomicResourceRepo,
            context: Optional[dict] = None) -> "AnnotationPipeline":

        pipeline = AnnotationPipeline(pipeline_config, repository)

        if pipeline_config.effect_annotators:
            for annotator_config in pipeline_config.effect_annotators:
                annotator_type = annotator_config["annotator"]

                gene_models_id = annotator_config["gene_models"]
                genome_id = annotator_config["genome"]
                override = annotator_config.get("override")

                gene_models = repository.get_resource(gene_models_id)
                assert gene_models is not None, gene_models_id

                genome = repository.get_resource(genome_id)
                assert genome is not None, genome_id

                effect_annotator = AnnotatorFactory.make_effect_annotator(
                    annotator_type, gene_models, genome, override=override)
                pipeline.add_annotator(effect_annotator)

        if pipeline_config.liftover_annotators:
            for annotator_config in pipeline_config.liftover_annotators:
                chain_id = annotator_config["chain"]
                genome_id = annotator_config["target_genome"]
                chain = repository.get_resource(chain_id)
                genome = repository.get_resource(genome_id)
                annotator_type = annotator_config["annotator"]
                liftover_id = annotator_config["liftover"]
                override = annotator_config.get("override")
                annotator = AnnotatorFactory.make_liftover_annotator(
                    annotator_type, chain, genome, liftover_id, override
                )
                pipeline.add_annotator(annotator)

        if pipeline_config.score_annotators:
            for annotator_config in pipeline_config.score_annotators:
                score_id = annotator_config["resource"]
                liftover = annotator_config["liftover"]
                annotator_type = annotator_config["annotator"]
                override = annotator_config.get("override")
                gs = repository.get_resource(score_id)
                assert gs is not None, annotator_config

                annotator = AnnotatorFactory.make_score_annotator(
                    annotator_type, gs, liftover, override
                )
                pipeline.add_annotator(annotator)

        return pipeline

    @property
    def output_columns(self):
        return chain(
            annotator.output_columns for annotator in self.annotators)

    @property
    def annotation_schema(self) -> Schema:
        if self._annotation_schema is None:
            schema = Schema()
            for annotator in self.annotators:
                schema = Schema.concat_schemas(
                    schema, annotator.annotation_schema)
            self._annotation_schema = schema
        return self._annotation_schema

    def add_annotator(self, annotator: Annotator) -> None:
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)
        self._annotation_schema = None

    def annotate_allele(self, allele: Allele) -> dict:
        attributes = {}
        liftover_context = dict()
        for annotator in self.annotators:
            annotator.annotate_allele(
                attributes, allele, liftover_context)

        return attributes
