#!/usr/bin/env python
import logging
from copy import deepcopy
from itertools import chain

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.annotation_conf import annotation_conf_schema
from dae.annotation.tools.annotator_base import Annotator
from dae.annotation.tools.file_io_parquet import ParquetSchema
from dae.annotation.tools.utils import AnnotatorFactory


logger = logging.getLogger(__name__)


class AnnotationPipeline():
    def __init__(self, config, resource_db):
        self.annotators = []
        self.config = config
        self.resource_db = resource_db

    @staticmethod
    def build(pipeline_config_path, resource_db):
        pipeline_config = GPFConfigParser.load_config(
            pipeline_config_path, annotation_conf_schema
        )
        pipeline = AnnotationPipeline(pipeline_config, resource_db)
        for annotator in pipeline_config.score_annotators:
            score_id = annotator["resource"]
            liftover = annotator["liftover"]
            annotator_type = annotator["annotator"]
            override = annotator.get("override")
            gs = resource_db.get_resource(score_id)
            annotator = AnnotatorFactory.make_annotator(
                annotator_type, gs, liftover, override
            )
            pipeline.add_annotator(annotator)
        return pipeline

    @property
    def output_columns(self):
        return chain(
            annotator.output_columns for annotator in self.annotators)

    def add_annotator(self, annotator):
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)

    def produce_annotation_schema(self):
        cols = set()
        for annotator in self.annotators:
            cols.update(annotator.output_columns)
        return ParquetSchema.from_dict({"float": cols})

    def annotate_summary_variant(self, summary_variant):
        for alt_allele in summary_variant.alt_alleles:
            attributes = deepcopy(alt_allele.attributes)
            liftover_variants = dict()
            for annotator in self.annotators:
                annotator.annotate(attributes, alt_allele, liftover_variants)
            alt_allele.update_attributes(attributes)
