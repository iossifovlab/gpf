#!/usr/bin/env python
from __future__ import annotations

import logging
import copy
import yaml

from itertools import chain
from typing import Dict, List

from cerberus.validator import Validator
from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.aggregators import AGGREGATOR_SCHEMA

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotator_base import Annotator
from dae.annotation.schema import Schema
from dae.annotation.annotator_factory import AnnotatorFactory


logger = logging.getLogger(__name__)

ATTRIBUTES_SCHEMA = {
    "type": "dict",
    "coerce": "attributes",
    "schema": {
        "source": {"type": "string"},
        "destination": {"type": "string"},
    }
}

ATTRIBUTES_POS_AGGR_SCHEMA = copy.deepcopy(ATTRIBUTES_SCHEMA)
ATTRIBUTES_POS_AGGR_SCHEMA["schema"]["position_aggregator"] = \
    AGGREGATOR_SCHEMA

ATTRIBUTES_NP_AGGR_SCHEMA = copy.deepcopy(ATTRIBUTES_POS_AGGR_SCHEMA)
ATTRIBUTES_NP_AGGR_SCHEMA["schema"]["nucleotide_aggregator"] = \
    AGGREGATOR_SCHEMA


ANNOTATOR_SCHEMA = {
    "np_score": {
        "type": "dict",
        "coerce": "score_resources",
        "schema": {
            "resource_id": {
                "type": "string",
                "required": True,
            },
            "liftover_id": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "attributes": {
                "type": "list",
                "nullable": True,
                "default": None,
                "schema": ATTRIBUTES_NP_AGGR_SCHEMA
            }
        }
    },
    "position_score": {
        "type": "dict",
        "coerce": "score_resources",
        "schema": {
            "resource_id": {
                "type": "string",
                "required": True,
            },
            "liftover_id": {
                "type": "string",
                "nullable": True,
                "default": None
            },
            "attributes": {
                "type": "list",
                "nullable": True,
                "default": None,
                "schema": ATTRIBUTES_POS_AGGR_SCHEMA
            }
        }
    },
    "allele_score": {
        "type": "dict",
        "coerce": "score_resources",
        "schema": {
            "resource_id": {
                "type": "string",
                "required": True,
            },
            "liftover_id": {
                "type": "string",
                "nullable": True,
            },
            "attributes": {
                "type": "list",
                "nullable": True,
                "default": None,
                "schema": ATTRIBUTES_SCHEMA
            }
        }
    },

    "effect_annotator": {
        "type": "dict",
        "coerce": "effect_annotator",
        "allow_unknown": True,

        "schema": {
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
    },

    "liftover_annotator": {
        "type": "dict",
        "schema": {
            "resource_id": {
                "type": "string",
                "required": True,
            },
            "liftover_id": {
                "type": "string",
                "required": True,
            },
            "target_genome": {
                "type": "string",
                "required": True,
            }
        }
    },

}


class AnnotationConfigValidator(Validator):

    def _normalize_coerce_score_resources(self, value):
        print("coerce score resource", value)
        if isinstance(value, str):
            return {
                "resource_id": value
            }

        return value

    def _normalize_coerce_effect_annotator(self, value):
        if isinstance(value, str):
            return {}

        return value

    def _normalize_coerce_attributes(self, value):
        if isinstance(value, str):
            return {
                "source": value,
                "destination": value,
            }
        elif isinstance(value, dict):
            if "source" in value and "destination" not in value:
                value["destination"] = value["source"]
            return value
        return value


class AnnotationConfigParser:

    @classmethod
    def validate(cls, pipeline_config: List[Dict]) -> List[Dict]:

        from pprint import pprint
        pprint(pipeline_config)
        result = []

        for annotator_config in pipeline_config:
            validator = AnnotationConfigValidator(ANNOTATOR_SCHEMA)
            if isinstance(annotator_config, str):
                annotator_config = {
                    annotator_config: {}
                }
            if not validator.validate(annotator_config):
                logger.error(
                    f"can't process annotator configuration: "
                    f"{validator.errors}")
                raise ValueError(f"{validator.errors}")

            document = validator.document
            assert isinstance(document, dict)
            assert len(document) == 1
            annotator_type, annotator_config = next(iter(document.items()))
            assert isinstance(annotator_config, dict)

            annotator_config["annotator_type"] = annotator_type
            result.append(Box(annotator_config))

        return result

    @classmethod
    def parse(cls, content: str) -> List[Dict]:
        pipeline_config = yaml.safe_load(content)
        if pipeline_config is None:
            logger.warning("empty annotation pipeline configuration")
            return []
        return cls.validate(pipeline_config)

    @classmethod
    def parse_config_file(cls, filename: str) -> List[Dict]:
        with open(filename, "rt") as infile:
            content = infile.read()
            return cls.parse(content)


class AnnotationPipelineContext:
    def get_reference_genome(self):
        return None

    def get_gene_models(self):
        return None


class AnnotationPipeline():
    def __init__(self, config, repository):
        self.annotators: List[Annotator] = []
        self.config: dict = config
        self.repository: GenomicResourceRepo = repository
        self._annotation_schema = None

    @classmethod
    def build_pipeline(
            cls,
            pipeline_config: List[Dict],
            grr: GenomicResourceRepo,
            context: AnnotationPipelineContext) -> AnnotationPipeline:

        pipeline = AnnotationPipeline(pipeline_config, grr)

        for annotator_config in pipeline_config:
            annotator = AnnotatorFactory.build(annotator_config, grr, context)
            pipeline.add_annotator(annotator)

    @staticmethod
    def construct_pipeline_ivan(pipeline: AnnotationPipeline,
                                context: AnnotationPipelineContext):
        # pipeline_config = pipeline.config
        # grr_repository = pipeline.repository
        pass

    @staticmethod
    def construct_pipeline_lubo(pipeline: AnnotationPipeline,
                                context: AnnotationPipelineContext):
        pipeline_config = pipeline.config
        grr_repository = pipeline.repository

        if pipeline_config.effect_annotators:
            for annotator_config in pipeline_config.effect_annotators:
                annotator_type = annotator_config["annotator"]

                if "gene_models" in annotator_config:
                    gene_models_id = annotator_config["gene_models"]
                    gene_models = grr_repository.get_resource(gene_models_id)
                    assert gene_models is not None, gene_models_id
                    # TODO: raise appropriate exception
                else:
                    gene_models = context.get_gene_models()
                    # TODO: raise excpetion if context is null
                    # or if genome is null

                if "genome" in annotator_config:
                    genome_id = annotator_config["genome"]
                    genome = grr_repository.get_resource(genome_id)
                    assert genome is not None, genome_id
                    # TODO: raise appropriate exception
                else:
                    genome = context.get_reference_genome()
                    # TODO: raise excpetion if context is null
                    # or if genome is null
                override = annotator_config.get("override")

                effect_annotator = AnnotatorFactory.make_effect_annotator(
                    annotator_type, gene_models, genome, override=override)
                pipeline.add_annotator(effect_annotator)

        if pipeline_config.liftover_annotators:
            for annotator_config in pipeline_config.liftover_annotators:
                chain_id = annotator_config["chain"]
                genome_id = annotator_config["target_genome"]
                chain = grr_repository.get_resource(chain_id)
                genome = grr_repository.get_resource(genome_id)
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
                gs = grr_repository.get_resource(score_id)
                assert gs is not None, annotator_config

                annotator = AnnotatorFactory.make_score_annotator(
                    annotator_type, gs, liftover, override
                )
                pipeline.add_annotator(annotator)

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


            Pipeline_config is a list. Each element is either a dict or a string.
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
        if pipeline_config is None:
            assert pipeline_config_file is not None
            pipeline_config = AnnotationPipeline.load_and_parse(
                pipeline_config_file)
        else:
            assert pipeline_config_file is None

        if not grr_repository:
            grr_repository = build_genomic_resource_repository(
                definition=grr_repository_definition,
                file_name=grr_repository_file)
        else:
            assert grr_repository_file is None
            assert grr_repository_definition is None

        pipeline = AnnotationPipeline(pipeline_config, grr_repository)

        if "score_annotators" in pipeline_config or \
                pipeline_config.get("effect_annotators") or \
                pipeline_config.get("liftover_annotators"):
            AnnotationPipeline.construct_pipeline_lubo(pipeline, context)
        else:
            AnnotationPipeline.construct_pipeline_ivan(pipeline, context)
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
