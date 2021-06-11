#!/usr/bin/env python

import logging

from typing import List


from dae.annotation.tools.annotator_base import (
    AnnotatorBase,
    CompositeVariantAnnotator,
)
from dae.configuration.gpf_config_parser import FrozenBox
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.file_io_parquet import ParquetSchema

from dae.annotation.tools.utils import AnnotatorFactory


logger = logging.getLogger(__name__)


class PipelineAnnotator(CompositeVariantAnnotator):

    ANNOTATION_SCHEMA_EXCLUDE = [
        "effect_gene_genes",
        "effect_gene_types",
        "effect_genes",
        "effect_details_transcript_ids",
        "effect_details_details",
        "effect_details",
        "OLD_effectType",
        "OLD_effectGene",
        "OLD_effectDetails",
    ]

    def build_annotation_schema(self):
        annotation_schema = ParquetSchema.from_arrow(ParquetSchema.BASE_SCHEMA)
        self.collect_annotator_schema(annotation_schema)
        for schema_key in self.ANNOTATION_SCHEMA_EXCLUDE:
            if schema_key in annotation_schema:
                del annotation_schema[schema_key]
        return annotation_schema
        # schema = annotation_schema.to_arrow()
        # return schema

    def __init__(self, config, genomes_db):
        super(PipelineAnnotator, self).__init__(config, genomes_db)
        self.virtual_columns: List[str] = list(config.virtual_columns)

    @staticmethod
    def build(config_file, gpf_instance):
        genomes_db = gpf_instance.genomes_db
        pipeline_config = \
            AnnotationConfigParser.read_and_parse_file_configuration(
                config_file
            )

        pipeline = PipelineAnnotator(pipeline_config, genomes_db)
        output_columns = list(pipeline.config.output_columns)
        for score in pipeline_config.genomic_scores:
            score_id = score["id"]
            liftover = score["liftover"]
            gs = gpf_instance.find_genomic_score(score_id)
            annotator = AnnotatorFactory.make_annotator(
                gs.config, genomes_db, liftover
            )
            pipeline.add_annotator(annotator)
            output_columns.extend([
                col for col in annotator.config.output_columns
                if col not in output_columns
            ])

        # FIXME
        # The lines below are a hack to allow modification
        # of the "output_columns" key in an otherwise frozen Box
        # This should be fixed properly when the annotation pipeline
        # module is refactored
        pipeline_config = pipeline.config.to_dict()
        pipeline_config["output_columns"] = output_columns
        pipeline.config = FrozenBox(pipeline_config)

        return pipeline

    def add_annotator(self, annotator):
        assert isinstance(annotator, AnnotatorBase)
        self.virtual_columns.extend(annotator.config.virtual_columns)
        self.annotators.append(annotator)

    def collect_annotator_schema(self, schema):
        super(PipelineAnnotator, self).collect_annotator_schema(schema)
        if self.virtual_columns:
            for vcol in self.virtual_columns:
                schema.remove_column(vcol)
