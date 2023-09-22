"""Factory for creation of annotation pipeline."""

# import collections
from collections import Counter
import logging
import copy
import fnmatch
from textwrap import dedent
from typing import List, Dict, Optional, Callable, Any

import yaml

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import ValueTransformAnnotatorDecorator
from dae.annotation.annotation_pipeline import \
    InputAnnotableAnnotatorDecorator

logger = logging.getLogger(__name__)


_ANNOTATOR_FACTORY_REGISTRY: dict[
    str, Callable[[AnnotationPipeline, AnnotatorInfo], Annotator]] = {}
_EXTENTIONS_LOADED = False


def _load_annotator_factory_plugins() -> None:
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
    factory: Callable[[AnnotationPipeline, AnnotatorInfo], Annotator]
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
        logger.warning("overwriting annotator type: %s", annotator_type)
    _ANNOTATOR_FACTORY_REGISTRY[annotator_type] = factory


class AnnotationConfigParser:
    """Parser for annotation configuration."""

    @staticmethod
    def normalize(pipeline_config: List[Any]) -> List[Dict]:
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
    def query_resources(
        annotator_type: str, wildcard: str, grr: GenomicResourceRepo
    ) -> list[str]:
        """Collect resources matching a given query."""
        result = []
        labels_query: dict[str, str] = {}

        # Handle querying by labels
        if wildcard.endswith("]"):
            assert "[" in wildcard
            wildcard, raw_labels = wildcard.split("[")
            labels = raw_labels.strip("]").split(" and ")
            for label in labels:
                k, v = label.split("=")
                labels_query[k] = v

        for resource in grr.get_all_resources():
            if (resource.get_type() == annotator_type
               and fnmatch.fnmatch(resource.get_id(), wildcard)
               and (not labels_query
                    or labels_query.items() <= resource.get_labels().items())):
                result.append(resource.get_id())

        return result

    @staticmethod
    def parse_minimal(raw: str, idx: int) -> AnnotatorInfo:
        """Parse a minimal-form annotation config."""
        return AnnotatorInfo(raw, [], {}, annotator_id=f"#{idx}")

    @staticmethod
    def parse_short(
        raw: dict[str, Any], idx: int,
        grr: Optional[GenomicResourceRepo] = None,
    ) -> list[AnnotatorInfo]:
        """Parse a short-form annotation config."""
        ann_type, ann_details = next(iter(raw.items()))
        if "*" in ann_details:
            assert grr is not None
            matching_resources = AnnotationConfigParser.query_resources(
                ann_type, ann_details, grr
            )
            return [
                AnnotatorInfo(
                    ann_type, [], {"resource_id": resource},
                    annotator_id=f"#{idx}-{resource}"
                )
                for resource in matching_resources
            ]
        return [
            AnnotatorInfo(
                ann_type, [], {"resource_id": ann_details},
                annotator_id=f"#{idx}"
            )
        ]

    @staticmethod
    def parse_complete(raw: dict[str, Any], idx: int) -> AnnotatorInfo:
        """Parse a full-form annotation config."""
        ann_type, ann_details = next(iter(raw.items()))
        attributes = []
        if "attributes" in ann_details:
            attributes = AnnotationConfigParser.parse_raw_attributes(
                ann_details["attributes"]
            )
        parameters = {k: v for k, v in ann_details.items()
                      if k != "attributes"}
        return AnnotatorInfo(
            ann_type, attributes, parameters, annotator_id=f"#{idx}"
        )

    @staticmethod
    def parse_raw(
        pipeline_raw_config: Optional[list[dict[str, Any]]],
        grr: Optional[GenomicResourceRepo] = None
    ) -> list[AnnotatorInfo]:
        """Parse raw dictionary annotation pipeline configuration."""
        if pipeline_raw_config is None:
            logger.warning("empty annotation pipeline configuration")
            return []

        if not isinstance(pipeline_raw_config, list):
            raise AnnotationConfigurationError(
                "The annotation is not a list of annotator configurations.")

        result = []
        for idx, raw_cfg in enumerate(pipeline_raw_config):
            if isinstance(raw_cfg, str):
                # the minimal annotator configuration form
                result.append(
                    AnnotationConfigParser.parse_minimal(raw_cfg, idx)
                )
                continue
            if isinstance(raw_cfg, dict):
                ann_details = next(iter(raw_cfg.values()))
                if isinstance(ann_details, str):
                    # the short annotator configuation form
                    result.extend(AnnotationConfigParser.parse_short(
                        raw_cfg, idx, grr
                    ))
                    continue
                if isinstance(ann_details, dict):
                    # the complete annotator configuration form
                    result.append(
                        AnnotationConfigParser.parse_complete(raw_cfg, idx)
                    )
                    continue
            raise AnnotationConfigurationError(dedent(f"""
                Incorrect annotator configuation form: {raw_cfg}.
                The allowed forms are:
                    * minimal
                        - <annotator type>
                    * short
                        - <annotator type>: <resource_id_pattern>
                    * complete without attributes
                        - <annotator type>:
                            <param1>: <value1>
                            ...
                    * complete with attributes
                        - <annotator type>:
                            <param1>: <value1>
                            ...
                            attributes:
                            - <att1 config>
                            ....
            """))
        return result

    @staticmethod
    def parse_str(
        content: str, source_file_name: Optional[str] = None,
        grr: Optional[GenomicResourceRepo] = None
    ) -> list[AnnotatorInfo]:
        """Parse annotation pipeline configuration string."""
        try:
            pipeline_raw_config = yaml.safe_load(content)
        except Exception as error:  # pylint: disable=broad-except
            if source_file_name is None:
                raise AnnotationConfigurationError(
                    f"The pipeline configuration {content} is an invalid yaml "
                    "string.", error) from error
            raise AnnotationConfigurationError(
                f"The pipeline configuration file {source_file_name} is "
                "an invalid yaml file.", error) from error

        return AnnotationConfigParser.parse_raw(pipeline_raw_config, grr=grr)

    @staticmethod
    def parse_config_file(
        filename: str, grr: Optional[GenomicResourceRepo]
    ) -> List[AnnotatorInfo]:
        """Parse annotation pipeline configuration file."""
        logger.info("loading annotation pipeline configuration: %s", filename)
        try:
            with open(filename, "rt", encoding="utf8") as infile:
                content = infile.read()
        except Exception as error:
            raise AnnotationConfigurationError(
                f"Problem reading the contents of the {filename} file.",
                error) from error

        return AnnotationConfigParser.parse_str(content, grr=grr)

    @staticmethod
    def parse_raw_attribute_config(
            raw_attribute_config: dict[str, Any]) -> AttributeInfo:
        """Parse annotation attribute raw configuration."""
        attribute_config = copy.deepcopy(raw_attribute_config)
        if "destination" in attribute_config:
            logger.warning(
                "usage of 'destination' in annotators attribute configuration "
                "is deprecated; use 'name' instead")
            name = attribute_config.get("destination")
            attribute_config.pop("destination")
            attribute_config["name"] = name

        name = attribute_config.get("name")
        source = attribute_config.get("source")

        if name is None and source is None:
            raise ValueError(f"The raw attribute configuraion "
                             f"{attribute_config} has neigther "
                             "name nor source.")

        name = name if name else source
        source = source if source else name
        internal = bool(attribute_config.get("internal", False))

        assert source is not None
        if not isinstance(name, str):
            message = "The name for in an attribute " + \
                      f"config {attribute_config} should be a string"
            raise ValueError(message)

        parameters = {k: v for k, v in attribute_config.items()
                      if k not in ["name", "source", "internal"]}
        return AttributeInfo(name, source, internal, parameters)

    @staticmethod
    def parse_raw_attributes(
            raw_attributes_config: Any) -> list[AttributeInfo]:
        """Parse annotator pipeline attribute configuration."""
        if not isinstance(raw_attributes_config, list):
            message = "The attributes parameters should be a list."
            raise ValueError(message)

        attribute_config = []
        for raw_attribute_config in raw_attributes_config:
            if isinstance(raw_attribute_config, str):
                raw_attribute_config = {"name": raw_attribute_config}
            attribute_config.append(
                AnnotationConfigParser.parse_raw_attribute_config(
                    raw_attribute_config))
        return attribute_config


class AnnotationConfigurationError(ValueError):
    pass


def build_annotation_pipeline(
        pipeline_config: Optional[list[AnnotatorInfo]] = None,
        pipeline_config_raw: Optional[list[dict]] = None,
        pipeline_config_file: Optional[str] = None,
        pipeline_config_str: Optional[str] = None,
        grr_repository: Optional[GenomicResourceRepo] = None,
        grr_repository_file: Optional[str] = None,
        grr_repository_definition: Optional[dict] = None,
        allow_repeated_attributes: bool = False,
) -> AnnotationPipeline:
    """Build an annotation pipeline."""
    if not grr_repository:
        grr_repository = build_genomic_resource_repository(
            definition=grr_repository_definition,
            file_name=grr_repository_file)
    else:
        assert grr_repository_file is None
        assert grr_repository_definition is None

    if pipeline_config_file is not None:
        assert pipeline_config is None
        assert pipeline_config_raw is None
        assert pipeline_config_str is None
        pipeline_config = AnnotationConfigParser.parse_config_file(
            pipeline_config_file, grr=grr_repository)
    elif pipeline_config_str is not None:
        assert pipeline_config_raw is None
        assert pipeline_config is None
        pipeline_config = AnnotationConfigParser.parse_str(
            pipeline_config_str, grr=grr_repository)
    elif pipeline_config_raw is not None:
        assert pipeline_config is None
        pipeline_config = AnnotationConfigParser.parse_raw(
            pipeline_config_raw, grr=grr_repository)
    assert pipeline_config is not None

    pipeline = AnnotationPipeline(grr_repository)

    for annotator_config in pipeline_config:
        try:
            builder = get_annotator_factory(annotator_config.type)
            annotator = builder(pipeline, annotator_config)
            annotator = InputAnnotableAnnotatorDecorator.decorate(annotator)
            annotator = ValueTransformAnnotatorDecorator.decorate(annotator)
            check_for_unused_parameters(annotator_config)
            check_for_repeated_attributes_in_annotator(annotator_config)
            pipeline.add_annotator(annotator)
        except ValueError as value_error:
            raise AnnotationConfigurationError(
                f"The {annotator_config.annotator_id} annotator"
                f" configuration is incorrect: ",
                value_error) from value_error

    check_for_repeated_attributes_in_pipeline(
        pipeline, allow_repeated_attributes
    )

    return pipeline


def check_for_repeated_attributes_in_annotator(
    annotator_config: AnnotatorInfo
) -> None:
    """Check for repeated attributes in annotator configuration."""
    annotator_names_list = [att.name for att in annotator_config.attributes]
    annotator_names_set = set(annotator_names_list)
    if len(annotator_names_set) < len(annotator_names_list):
        repeated_annotator_names = ",".join(sorted(
            [att for att, cnt in Counter(annotator_names_list).items()
             if cnt > 1]))
        raise ValueError("The annotator has repeated attributes: "
                         f"{repeated_annotator_names}")


def check_for_repeated_attributes_in_pipeline(
    pipeline: AnnotationPipeline, allow_repeated_attributes: bool = False
) -> None:
    """Check for repeated attributes in pipeline configuration."""
    pipeline_names_set = Counter(att.name for att in pipeline.get_attributes())
    repeated_attributes = {
        att for att, cnt in Counter(pipeline_names_set).items() if cnt > 1
    }
    if repeated_attributes:
        attrs_err_msg = ",".join(sorted(repeated_attributes))
        if not allow_repeated_attributes:
            raise AnnotationConfigurationError(
                "The annotator repeats the attributes "
                f"{attrs_err_msg} that are already in "
                f"the pipeline"
            )
        resolve_repeated_attributes(pipeline, repeated_attributes)


def resolve_repeated_attributes(
    pipeline: AnnotationPipeline, repeated_attributes: set[str]
) -> None:
    """Resolve repeated attributes in pipeline configuration via renaming."""
    for rep in repeated_attributes:
        for annotator in pipeline.annotators:
            for attribute in annotator.attributes:
                if attribute.name == rep:
                    attribute.name = f"{attribute.name}_({annotator.get_info().annotator_id})"  # noqa


def check_for_unused_parameters(info: AnnotatorInfo) -> None:
    """Check annotator configuration for unused parameters."""
    unused_annotator_parameters = info.parameters.get_unused_keys()
    if unused_annotator_parameters:
        raise ValueError("The are unused annotator parameters: "
                         f"{unused_annotator_parameters}")

    for att in info.attributes:
        unused_params = att.parameters.get_unused_keys()
        if unused_params:
            raise ValueError("There are unused annotator attribute "
                             f"parameters: {','.join(sorted(unused_params))}")
