#!/usr/bin/env python
import logging
import pyarrow as pa

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.annotation_conf import annotation_conf_schema
from dae.annotation.tools.annotator_base import Annotator, CompositeAnnotator
from dae.annotation.tools.utils import AnnotatorFactory


logger = logging.getLogger(__name__)


class PipelineAnnotator(CompositeAnnotator):
    def __init__(self, config, genomes_db):
        super().__init__(config, genomes_db)

    @staticmethod
    def build(pipeline_config_path, gpf_instance):
        genomes_db = gpf_instance.genomes_db
        pipeline_config = GPFConfigParser.load_config(
            pipeline_config_path, annotation_conf_schema
        )
        pipeline = PipelineAnnotator(pipeline_config, genomes_db)
        for score in pipeline_config.genomic_scores:
            score_id = score["id"]
            liftover = score["liftover"]
            gs = gpf_instance.find_genomic_score(score_id)
            annotator = AnnotatorFactory.make_annotator(
                gs.config, genomes_db, liftover
            )
            pipeline.add_annotator(annotator)
        return pipeline

    def add_annotator(self, annotator):
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)

    def produce_annotation_schema(self):
        cols = set()
        for annotator in self.annotators:
            cols.update(annotator.output_columns)

        return pa.schema([pa.field(col, pa.float32()) for col in cols])
