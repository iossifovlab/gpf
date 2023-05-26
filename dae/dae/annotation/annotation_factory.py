"""Factory for creation of annotation pipeline."""

import logging
from typing import List, Dict, Optional, Callable, Any

import yaml

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotation_pipeline import AnnotationPipeline, InputAnnotableAnnotatorDecorator, ValueTransormAnnotatorDecorator
from dae.annotation.annotation_pipeline import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import Annotator

logger = logging.getLogger(__name__)


_ANNOTATOR_FACTORY_REGISTRY: dict[
    str, Callable[[AnnotationPipeline, dict[str, Any]], Annotator]] = {}
_EXTENTIONS_LOADED = False


def _load_annotator_factory_plugins():
    # pylint: disable=global-statement
    global _EXTENTIONS_LOADED
    if _EXTENTIONS_LOADED:
        return
    # pylint: disable=import-outside-toplevel
    from importlib_metadata import entry_points
    discovered_entries = entry_points(group="dae.annotation.annotators")
    for entry in discovered_entries:
        annotator_type = entry.name
        factory = entry.load()
        if annotator_type in _ANNOTATOR_FACTORY_REGISTRY:
            logger.warning(
                "overwriting annotator type: %s", annotator_type)
        _ANNOTATOR_FACTORY_REGISTRY[annotator_type] = factory
    _EXTENTIONS_LOADED = True


def get_annotator_factory(
    annotator_type: str
) -> Callable[[AnnotationPipeline, AnnotatorInfo], Annotator]:
    """Find and return a factory function for creation of an annotator type.

    If the specified annotator type is not found, this function raises
    `ValueError` exception.

    :return: the annotator factory for the specified annotator type.
    :raises ValueError: when can't find an annotator  factory for the
        specified annotator type.
    """
    _load_annotator_factory_plugins()
    if annotator_type not in _ANNOTATOR_FACTORY_REGISTRY:
        raise ValueError(f"unsupported annotator type: {annotator_type}")
    return _ANNOTATOR_FACTORY_REGISTRY[annotator_type]


def get_available_annotator_types() -> List[str]:
    """Return the list of all registered annotator factory types."""
    _load_annotator_factory_plugins()
    return list(_ANNOTATOR_FACTORY_REGISTRY.keys())


def register_annotator_factory(
    annotator_type: str,
    factory: Callable[[AnnotationPipeline, dict[str, Any]], Annotator]
) -> None:
    """Register additional annotator factory.

    By default all genotype storage factories should be registered at
    `[dae.genotype_storage.factories]` extenstion point. All registered
    factories are loaded automatically. This function should be used if you
    want to bypass extension point mechanism and register addition genotype
    storage factory programatically.
    """
    _load_annotator_factory_plugins()
    if annotator_type in _ANNOTATOR_FACTORY_REGISTRY:
        logger.warning("overwriting genotype storage type: %s", annotator_type)
    _ANNOTATOR_FACTORY_REGISTRY[annotator_type] = factory


class AnnotationConfigParser:
    """Parser for annotation configuration."""

    @staticmethod
    def normalize(pipeline_config: List[Dict]) -> List[Dict]:
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

    @staticmethod
    def parse_raw(pipeline_raw_config: list[dict]) -> list[AnnotatorInfo]:
        pipeline_normalized_config = \
            AnnotationConfigParser.normalize(pipeline_raw_config)

        r = []
        for annotator_raw_config in pipeline_normalized_config:
            annotator_type = annotator_raw_config["annotator_type"]

            attributes = []
            if "attributes" in annotator_raw_config:
                attributes = \
                    AnnotationConfigParser.parse_raw_attributes(
                        annotator_raw_config["attributes"])
            parameters = {k: v for k, v in annotator_raw_config.items()
                          if k not in ["annotator_type", "attributes"]}
            r.append(AnnotatorInfo(annotator_type, attributes, parameters, []))
        return r

    @staticmethod
    def parse_str(content: str) -> list[AnnotatorInfo]:
        pipeline_raw_config = yaml.safe_load(content)
        if pipeline_raw_config is None:
            logger.warning("empty annotation pipeline configuration")
            return []
        return AnnotationConfigParser.parse_raw(pipeline_raw_config)

    @staticmethod
    def parse_config_file(filename: str) -> List[AnnotatorInfo]:
        logger.info("loading annotation pipeline configuration: %s", filename)
        with open(filename, "rt", encoding="utf8") as infile:
            content = infile.read()
            return AnnotationConfigParser.parse_str(content)

    @staticmethod
    def parse_raw_attribute_config(raw_attribute_config: dict[str, Any]) \
            -> AttributeInfo:
        name = raw_attribute_config.get("destination")
        source = raw_attribute_config.get("source")

        if name is None and source is None:
            message = f"The raw attribute configuraion {raw_attribute_config} " + \
                "has neigther destination nor source."
            raise Exception(message)

        name = name if name else source
        source = source if source else name
        internal = bool(raw_attribute_config.get("internal", False))

        assert source is not None
        if not isinstance(name, str):
            message = "The destination for in an attribute " + \
                      f"config {raw_attribute_config} should be a string"
            raise Exception(message)

        parameters = {k: v for k, v in raw_attribute_config.items()
                      if k not in ["destination", "source", "internal"]}
        return AttributeInfo(name, source, internal, parameters)

    @staticmethod
    def parse_raw_attributes(raw_attributes_config: Any) \
            -> list[AttributeInfo]:
        if not isinstance(raw_attributes_config, list):
            message = "The attributes parameters should be a list."
            raise Exception(message)

        attribute_config = []
        for raw_attribute_config in raw_attributes_config:
            if isinstance(raw_attribute_config, str):
                raw_attribute_config = {"destination": raw_attribute_config}
            attribute_config.append(
                AnnotationConfigParser.parse_raw_attribute_config(
                    raw_attribute_config))
        return attribute_config


def build_annotation_pipeline(
        pipeline_config: Optional[list[AnnotatorInfo]] = None,
        pipeline_config_raw: Optional[list[dict]] = None,
        pipeline_config_file: Optional[str] = None,
        pipeline_config_str: Optional[str] = None,
        grr_repository: Optional[GenomicResourceRepo] = None,
        grr_repository_file: Optional[str] = None,
        grr_repository_definition: Optional[dict] = None
) -> AnnotationPipeline:
    """Build an annotation pipeline."""
    if pipeline_config_file is not None:
        assert pipeline_config is None
        assert pipeline_config_raw is None
        assert pipeline_config_str is None
        pipeline_config = AnnotationConfigParser.parse_config_file(
            pipeline_config_file)
    elif pipeline_config_str is not None:
        assert pipeline_config_raw is None
        assert pipeline_config is None
        pipeline_config = AnnotationConfigParser.parse_str(pipeline_config_str)
    elif pipeline_config_raw is not None:
        assert pipeline_config is None
        pipeline_config = AnnotationConfigParser.parse_raw(pipeline_config_raw)
    assert pipeline_config is not None
    if not grr_repository:
        grr_repository = build_genomic_resource_repository(
            definition=grr_repository_definition,
            file_name=grr_repository_file)
    else:
        assert grr_repository_file is None
        assert grr_repository_definition is None

    pipeline = AnnotationPipeline(grr_repository)

    for annotator_config in pipeline_config:
        builder = get_annotator_factory(annotator_config.type)
        annotator = builder(pipeline, annotator_config)
        annotator = InputAnnotableAnnotatorDecorator.decorate(annotator)
        annotator = ValueTransormAnnotatorDecorator.decorate(annotator)
        pipeline.add_annotator(annotator)

    return pipeline
