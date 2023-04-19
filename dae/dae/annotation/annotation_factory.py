"""Factory for creation of annotation pipeline."""

import logging
from typing import List, Dict, Optional

import yaml

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotation_pipeline import AnnotationPipeline

from .score_annotator import build_allele_score_annotator, \
    build_np_score_annotator, build_position_score_annotator
from .effect_annotator import build_effect_annotator
from .liftover_annotator import build_liftover_annotator
from .normalize_allele_annotator import build_normalize_allele_annotator
from .gene_score_annotator import build_gene_score_annotator


logger = logging.getLogger(__name__)


ANNOTATOR_BUILDER_REGISTRY = {
    "position_score": build_position_score_annotator,
    "np_score": build_np_score_annotator,
    "allele_score": build_allele_score_annotator,
    "effect_annotator": build_effect_annotator,
    "liftover_annotator": build_liftover_annotator,
    "normalize_allele_annotator": build_normalize_allele_annotator,
    "gene_score_annotator": build_gene_score_annotator,
}


class AnnotationConfigParser:
    """Parser for annotation configuration."""

    @classmethod
    def normalize(cls, pipeline_config: List[Dict]) -> List[Dict]:
        """Return a normalized annotation pipeline configuration."""
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
            result.append(config)

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
        logger.info("loading annotation pipeline configuration: %s", filename)
        with open(filename, "rt", encoding="utf8") as infile:
            content = infile.read()
            return cls.parse(content)


def build_annotation_pipeline(
        pipeline_config: Optional[List[Dict]] = None,
        pipeline_config_file: Optional[str] = None,
        pipeline_config_str: Optional[str] = None,
        grr_repository: Optional[GenomicResourceRepo] = None,
        grr_repository_file: Optional[str] = None,
        grr_repository_definition: Optional[dict] = None
) -> AnnotationPipeline:
    """Build an annotation pipeline."""
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

    pipeline = AnnotationPipeline(pipeline_config, grr_repository)

    for annotator_config in pipeline_config:
        try:
            annotator_type = annotator_config["annotator_type"]
        except KeyError as ex:
            raise ValueError(
                "The pipeline config element has no annotator_type!") from ex
        try:
            builder = ANNOTATOR_BUILDER_REGISTRY[annotator_type]
        except KeyError as ex:
            raise ValueError(f"Unknonwn annotator type {annotator_type}.") \
                from ex
        annotator = builder(pipeline, annotator_config)
        pipeline.add_annotator(annotator)

    return pipeline
