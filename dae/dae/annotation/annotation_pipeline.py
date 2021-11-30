#!/usr/bin/env python
from __future__ import annotations

import logging
import yaml

from itertools import chain
from typing import Dict, List

from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources import build_genomic_resource_repository

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotator_base import Annotator
from dae.annotation.schema import Schema
from dae.annotation.annotator_factory import AnnotatorFactory
from dae.annotation.annotation_context import AnnotationPipelineContext

logger = logging.getLogger(__name__)


class AnnotationConfigParser:

    @classmethod
    def normalize(cls, pipeline_config: List[Dict]) -> List[Dict]:
        result = []

        for index, config in enumerate(pipeline_config):
            if isinstance(config, str):
                config = {
                    config: {}
                }

            assert isinstance(config, dict)
            assert len(config) == 1
            annotator_type, config = next(iter(config.items()))
            if not isinstance(config, dict):
                assert isinstance(config, str)
                # handle score annotators short form
                config = {"resource_id": config}

            assert isinstance(config, dict)
            if config.get("id") is None:
                config["id"] = str(index)

            config["annotator_type"] = annotator_type
            result.append(Box(config))

        return result

    @classmethod
    def parse(cls, content: str) -> List[Dict]:
        pipeline_config = yaml.safe_load(content)
        if pipeline_config is None:
            logger.warning("empty annotation pipeline configuration")
            return []
        return cls.normalize(pipeline_config)

    @classmethod
    def parse_config_file(cls, filename: str) -> List[Dict]:
        logger.info(f"loading annotation pipeline configuration: {filename}")
        with open(filename, "rt") as infile:
            content = infile.read()
            return cls.parse(content)


class AnnotationPipeline():
    def __init__(
            self, config: List[Dict],
            repository: GenomicResourceRepo,
            context: AnnotationPipelineContext):
        self.annotators: List[Annotator] = []
        self.config: dict = config
        self.repository: GenomicResourceRepo = repository
        self.context: AnnotationPipelineContext = context

        self._annotation_schema = None

    @classmethod
    def construct_pipeline(
            cls,
            pipeline_config: List[Dict],
            grr: GenomicResourceRepo,
            context: AnnotationPipelineContext) -> AnnotationPipeline:

        pipeline = AnnotationPipeline(pipeline_config, grr, context)

        for annotator_config in pipeline_config:
            annotator = AnnotatorFactory.build(pipeline, annotator_config)
            pipeline.add_annotator(annotator)

        return pipeline

    @staticmethod
    def build(
            pipeline_config: dict = None,
            pipeline_config_file: str = None,
            pipeline_config_str: str = None,
            grr_repository: GenomicResourceRepo = None,
            grr_repository_file: str = None,
            grr_repository_definition: str = None,
            context: AnnotationPipelineContext = None) -> "AnnotationPipeline":
        '''
            - np_score: <resource id>

            [ {"np_score":<resource id>} ]

            OR

            - np_score:
                resource_id: 7

            [ {"np_score":{"resource_id":7}} ]

            OR

            - np_score: <resource id1>
            - np_score: <resource id2>

            [ {"np_score":<resource id1>},
              {"np_score":<resource id2>} ]

            OR

            - np_score:
                resource_id: 7
                lift_over_id: bla
            - position_score:
                resource_id: 9
                attributes:
                    - a
                    - b

            [ {
                "np_score": {
                   "resource_id":7,
                   "lift_over_id": "bla" },
              },
              {
                "position_score": {
                    "resrouce_id": 9,
                    "attributes": ['a', 'b']
                }
              }
            ]


            Pipeline_config is a list. Each element is either a dict or a
            string.
            If it is a string, it specifies the annotator type with and empty
            configuration. If it is a dict, the dict must have only
            one entry. The key of that entry is the annotator type. The value
            of that entry is configuration for the annotator.



            It is a list of dictionaries.
            * Each dictionary has a filed 'annotator_type' whose value is a
              string.
            * Each dictionary may have have and annotoror_id, which if missinng
              will be set to the index of annotator.

            * Each dictionary can have a filed 'attributes' filed whose value
              is a list of dictionaries. These dictionaries have the following
              fields:
                source
                destination
                internal: boolean
                attribute_configuration_parameter_1
                attribute_configuration_parameter_...
              If 'attributes' is missing (or empty???) the Annotator should
              use its default attributes configuration.

            The additional parameters
            configure the annotator.


        '''
        if pipeline_config_file is not None:
            assert pipeline_config is None
            assert pipeline_config_str is None
            pipeline_config = AnnotationConfigParser.parse_config_file(
                pipeline_config_file)
        elif pipeline_config_str is not None:
            assert pipeline_config_file is None
            assert pipeline_config is None
            pipeline_config = AnnotationConfigParser.parse(pipeline_config_str)

        assert pipeline_config is not None

        if not grr_repository:
            grr_repository = build_genomic_resource_repository(
                definition=grr_repository_definition,
                file_name=grr_repository_file)
        else:
            assert grr_repository_file is None
            assert grr_repository_definition is None

        pipeline = AnnotationPipeline.construct_pipeline(
            pipeline_config, grr_repository, context)

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

    def annotate(self, annotatable: Annotatable) -> dict:
        attributes = {}
        liftover_context = dict()
        for annotator in self.annotators:
            annotator.annotate(
                attributes, annotatable, liftover_context)

        return attributes
