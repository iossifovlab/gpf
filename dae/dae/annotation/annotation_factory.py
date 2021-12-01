import logging
import yaml

from typing import List, Dict
from box import Box

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo

from .score_annotator import build_allele_score_annotator, \
    build_np_score_annotator, build_position_score_annotator
from .effect_annotator import build_effect_annotator
from .liftover_annotator import build_liftover_annotator
from .annotation_pipeline import AnnotationPipeline, AnnotationPipelineContext


logger = logging.getLogger(__name__)


ANNOTATOR_BUILDER_REGISTRY = {
    "position_score": build_position_score_annotator,
    "np_score": build_np_score_annotator,
    "allele_score": build_allele_score_annotator,
    "effect_annotator": build_effect_annotator,
    "liftover_annotator": build_liftover_annotator,
}


class AnnotationConfigParser:

    @classmethod
    def normalize(cls, pipeline_config: List[Dict]) -> List[Dict]:
        result = []

        for config in pipeline_config:
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


def build_annotation_pipeline(
        pipeline_config: List[Dict] = None,
        pipeline_config_file: str = None,
        pipeline_config_str: str = None,
        grr_repository: GenomicResourceRepo = None,
        grr_repository_file: str = None,
        grr_repository_definition: str = None,
        context: AnnotationPipelineContext = None) -> "AnnotationPipeline":

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

    pipeline = AnnotationPipeline(pipeline_config, grr_repository, context)

    for annotator_config in pipeline_config:
        annotator_type = annotator_config.get("annotator_type")
        builder = ANNOTATOR_BUILDER_REGISTRY.get(annotator_type)
        annotator = builder(pipeline, annotator_config)
        pipeline.add_annotator(annotator)

    return pipeline
