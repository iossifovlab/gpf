import copy
import fnmatch
import logging
from textwrap import dedent
from typing import Any, Optional, TypedDict, Union

import yaml

from dae.annotation.annotation_pipeline import (
    AnnotationPreambule,
    AnnotatorInfo,
    AttributeInfo,
)
from dae.genomic_resources.repository import (
    GenomicResource,
    GenomicResourceRepo,
)

logger = logging.getLogger(__name__)


class RawPreambule(TypedDict):
    summary: str
    description: str
    input_reference_genome: str
    metadata: dict[str, Any]


RawAnnotatorsConfig = list[dict[str, Any]]


class RawFullConfig(TypedDict):
    preambule: RawPreambule
    annotators: RawAnnotatorsConfig


RawPipelineConfig = Union[RawAnnotatorsConfig, RawFullConfig]


class AnnotationConfigurationError(ValueError):
    pass


class AnnotationConfigParser:
    """Parser for annotation configuration."""

    @staticmethod
    def match_labels_query(
        query: dict[str, str], resource_labels: dict[str, str],
    ) -> bool:
        """Check if the labels query for a wildcard matches."""
        for k, v in query.items():
            if k not in resource_labels \
               or not fnmatch.fnmatch(resource_labels[k], v):
                return False
        return True

    @staticmethod
    def query_resources(
        annotator_type: str, wildcard: str, grr: GenomicResourceRepo,
    ) -> list[str]:
        """Collect resources matching a given query."""
        labels_query: dict[str, str] = {}
        if wildcard.endswith("]"):
            assert "[" in wildcard
            wildcard, raw_labels = wildcard.split("[")
            labels = raw_labels.strip("]").split(" and ")
            for label in labels:
                k, v = label.split("=")
                labels_query[k] = v

        def match(resource: GenomicResource) -> bool:
            return (resource.get_type() == annotator_type
               and fnmatch.fnmatch(resource.get_id(), wildcard)
               and AnnotationConfigParser.match_labels_query(labels_query,
                                                             resource.get_labels()))

        return [resource.get_id()
                for resource in grr.get_all_resources()
                if match(resource)]

    @staticmethod
    def has_wildcard(string: str) -> bool:
        """Ascertain whether a string contains a valid wildcard."""
        # Check if at least one wildcard symbol is present
        # in the resource id itself, since '*' can also be used
        # in the label query as well (within square bracket)
        return "*" in string \
            and ("[" not in string or string.index("*") < string.index("["))

    @staticmethod
    def parse_minimal(raw: str, idx: int) -> AnnotatorInfo:
        """Parse a minimal-form annotation config."""
        return AnnotatorInfo(raw, [], {}, annotator_id=f"A{idx}")

    @staticmethod
    def parse_short(
        raw: dict[str, Any], idx: int,
        grr: Optional[GenomicResourceRepo] = None,
    ) -> list[AnnotatorInfo]:
        """Parse a short-form annotation config."""
        ann_type, ann_details = next(iter(raw.items()))
        if AnnotationConfigParser.has_wildcard(ann_details):
            assert grr is not None
            matching_resources = AnnotationConfigParser.query_resources(
                ann_type, ann_details, grr,
            )
            return [
                AnnotatorInfo(
                    ann_type, [], {"resource_id": resource},
                    annotator_id=f"A{idx}_{resource}",
                )
                for resource in matching_resources
            ]
        return [
            AnnotatorInfo(
                ann_type, [], {"resource_id": ann_details},
                annotator_id=f"A{idx}",
            ),
        ]

    @staticmethod
    def parse_complete(raw: dict[str, Any], idx: int) -> AnnotatorInfo:
        """Parse a full-form annotation config."""
        ann_type, ann_details = next(iter(raw.items()))
        attributes = []
        if "attributes" in ann_details:
            attributes = AnnotationConfigParser.parse_raw_attributes(
                ann_details["attributes"],
            )
        parameters = {k: v for k, v in ann_details.items()
                      if k != "attributes"}
        return AnnotatorInfo(
            ann_type, attributes, parameters, annotator_id=f"A{idx}",
        )

    @staticmethod
    def _parse_preambule(
        raw: RawPreambule,
        grr: Optional[GenomicResourceRepo] = None,
    ) -> Optional[AnnotationPreambule]:
        """Parse the preambule section of a pipeline config, if present."""
        if not set(raw.keys()) <= {
            "summary", "description", "input_reference_genome", "metadata",
        }:
            raise AnnotationConfigurationError

        if not isinstance(raw.get("summary", ""), str):
            raise TypeError("Preambule summary must be a string!")
        if not isinstance(raw.get("description", ""), str):
            raise TypeError("Preambule description must be a string!")
        if not isinstance(raw.get("input_reference_genome", ""), str):
            raise TypeError("Preambule reference genome id must be a string!")
        if not isinstance(raw.get("metadata", {}), dict):
            raise TypeError("Preambule metadata must be a dictionary!")

        genome_id = raw.get("input_reference_genome", "")
        genome = None
        if genome_id != "" and grr is not None:
            genome = grr.get_resource(genome_id)

        return AnnotationPreambule(
            raw.get("summary", ""),
            raw.get("description", ""),
            genome_id,
            genome,
            raw.get("metadata", {}),
        )

    @staticmethod
    def parse_raw(
        pipeline_raw_config: Optional[RawPipelineConfig],
        grr: Optional[GenomicResourceRepo] = None,
    ) -> tuple[Optional[AnnotationPreambule], list[AnnotatorInfo]]:
        """Parse raw dictionary annotation pipeline configuration."""
        if pipeline_raw_config is None:
            logger.warning("empty annotation pipeline configuration")
            return None, []

        if isinstance(pipeline_raw_config, dict):
            annotators = pipeline_raw_config["annotators"]
            preambule = AnnotationConfigParser._parse_preambule(
                pipeline_raw_config["preambule"], grr,
            )
        elif isinstance(pipeline_raw_config, list):
            annotators = pipeline_raw_config
            preambule = None
        else:
            raise AnnotationConfigurationError

        result = []
        for idx, raw_cfg in enumerate(annotators):
            if isinstance(raw_cfg, str):
                # the minimal annotator configuration form
                result.append(
                    AnnotationConfigParser.parse_minimal(raw_cfg, idx),
                )
                continue
            if isinstance(raw_cfg, dict):
                ann_details = next(iter(raw_cfg.values()))
                if isinstance(ann_details, str):
                    # the short annotator configuation form
                    result.extend(AnnotationConfigParser.parse_short(
                        raw_cfg, idx, grr,
                    ))
                    continue
                if isinstance(ann_details, dict):
                    # the complete annotator configuration form
                    result.append(
                        AnnotationConfigParser.parse_complete(raw_cfg, idx),
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
        return preambule, result

    @staticmethod
    def parse_str(
        content: str, source_file_name: Optional[str] = None,
        grr: Optional[GenomicResourceRepo] = None,
    ) -> tuple[Optional[AnnotationPreambule], list[AnnotatorInfo]]:
        """Parse annotation pipeline configuration string."""
        try:
            pipeline_raw_config = yaml.safe_load(content)
        except yaml.YAMLError as error:
            if source_file_name is None:
                raise AnnotationConfigurationError(
                    f"The pipeline configuration {content} is an invalid yaml "
                    "string.", error) from error
            raise AnnotationConfigurationError(
                f"The pipeline configuration file {source_file_name} is "
                "an invalid yaml file.", error) from error

        return AnnotationConfigParser.parse_raw(pipeline_raw_config, grr=grr)

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

        name = name or source
        source = source or name
        internal = bool(attribute_config.get("internal", False))

        assert source is not None
        if not isinstance(name, str):
            message = ("The name for in an attribute "
                       f"config {attribute_config} should be a string")
            raise TypeError(message)

        parameters = {k: v for k, v in attribute_config.items()
                      if k not in ["name", "source", "internal"]}
        return AttributeInfo(name, source, internal, parameters)

    @staticmethod
    def parse_raw_attributes(
            raw_attributes_config: Any) -> list[AttributeInfo]:
        """Parse annotator pipeline attribute configuration."""
        if not isinstance(raw_attributes_config, list):
            message = "The attributes parameters should be a list."
            raise TypeError(message)

        attribute_config = []
        for raw_attribute_config in raw_attributes_config:
            if isinstance(raw_attribute_config, str):
                raw_attribute_config = {"name": raw_attribute_config}
            attribute_config.append(
                AnnotationConfigParser.parse_raw_attribute_config(
                    raw_attribute_config))
        return attribute_config
