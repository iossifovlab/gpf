"""Provides base class for annotators."""
from __future__ import annotations

import logging
import abc

from typing import Any, Optional
from cerberus.validator import Validator  # type: ignore

from .annotatable import Annotatable
from .schema import Schema

logger = logging.getLogger(__name__)


ATTRIBUTES_SCHEMA = {
    "type": "dict",
    "coerce": "attributes",
    "allow_unknown": True,
    "schema": {
        "source": {"type": "string"},
        "destination": {"type": "string"},
        "internal": {
            "type": "boolean",
            "default": False,
        }
    }
}


class Annotator(abc.ABC):
    """Annotator provides a set of attrubutes for a given Annotatable."""

    class ConfigValidator(Validator):
        """Cerberus validation for annotators configuration."""

        def _normalize_coerce_attributes(self, value):
            if isinstance(value, str):
                return {
                    "source": value,
                    "destination": value,
                }
            if isinstance(value, dict):
                if "source" in value and "destination" not in value:
                    value["destination"] = value["source"]
                return value
            return value

    def __init__(self, config: dict):
        self.config = self.validate_config(config)
        self.input_annotatable = self.config.get("input_annotatable")
        self._annotation_schema: Optional[Schema] = None

    @classmethod
    @abc.abstractmethod
    def validate_config(cls, config: dict) -> dict:
        """Normalize and validate the annotation configuration.

        When validation passes returns the normalized and validated
        annotator configuration dict.

        When validation fails, raises ValueError.
        """
        return config

    @abc.abstractmethod
    def get_all_annotation_attributes(self) -> list[dict]:
        """Return list of all available attributes provided by the annotator.

        The result is a list of dicts. Each dict contains following
        attributes:

        * source: the name of the attribute
        * type: type of the attribute
        * desc: descripion of the attribute
        """
        return []

    def get_annotation_attribute(self, attribute_name) -> dict[str, str]:
        """Return configuration of an attribute."""
        for attribute in self.get_all_annotation_attributes():
            if attribute_name == attribute["name"]:
                return attribute
        message = f"can't find attribute {attribute_name} in annotator " \
            f"{self.annotator_type()}: {self.config}"
        logger.error(message)
        raise ValueError(message)

    @property
    def annotation_schema(self):
        """Return annotation schema."""
        if self._annotation_schema is None:
            schema = Schema()
            for attribute in self.get_annotation_config():
                if "destination" not in attribute:
                    attribute["destination"] = attribute["source"]

                annotation_attribute = self.get_annotation_attribute(
                    attribute["source"])

                source = Schema.Source(
                    self.annotator_type(),
                    annotator_config=self.config,
                    attribute_config=attribute)

                schema.create_field(
                    attribute["destination"],
                    py_type=annotation_attribute["type"],
                    internal=attribute.get("internal", False),
                    description=annotation_attribute["desc"],
                    source=source)

            self._annotation_schema = schema
        return self._annotation_schema

    @abc.abstractmethod
    def annotator_type(self) -> str:
        """Return annotator type."""

    @abc.abstractmethod
    def get_annotation_config(self) -> list[dict]:
        """Return annotation config."""

    @abc.abstractmethod
    def annotate(self, annotatable: Annotatable,
                 context: dict[str, Any]) -> dict[str, Any]:
        """Produce annotation attributes for an annotatable."""

    @abc.abstractmethod
    def close(self):
        """Close all resources used by the annotator."""

    @abc.abstractmethod
    def open(self) -> Annotator:
        """Prepare all resources needed by the annotator."""

    @abc.abstractmethod
    def is_open(self) -> bool:
        """Check if an annotator is open and ready."""

    @property
    @abc.abstractmethod
    def resources(self) -> set[str]:
        """Genomic resources used by the annotator."""

    def _empty_result(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for attr in self.get_annotation_config():
            result[attr["destination"]] = None
        return result

    def _remap_annotation_attributes(
            self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Remap the annotation attributes from source to destination.

        The method uses the annotation configuration and renames
        annotation attributes from their source name to destination.

        This implementation is suitable for most annotators and is used in
        the `AnnotatorBase` implementation.
        """
        attributes_config = self.get_annotation_config()
        for attr in attributes_config:
            destination = attr.get("destination", attr["source"])
            if destination == attr["source"]:
                continue
            attributes[attr["destination"]] = attributes[attr["source"]]
            del attributes[attr["source"]]
        return attributes

    def _get_annotatable_override(
            self, annotatable: Annotatable,
            context: dict[str, Any]) -> Optional[Annotatable]:
        """Find and return an annotatable override if configured.

        Otherwise returns the default annotatable.
        """
        if self.input_annotatable is None:
            return annotatable

        if self.input_annotatable not in context:
            raise ValueError(
                f"can't find input annotatable {self.input_annotatable} "
                f"in annotation context: {context}")
        override = context[self.input_annotatable]
        logger.debug(
            "input annotatable %s found %s.",
            self.input_annotatable, override)

        if override is None:
            logger.warning(
                "can't find input annotatable %s "
                "in annotation context: %s",
                self.input_annotatable, context)
            return None

        if not isinstance(override, Annotatable):
            raise ValueError(
                f"The object with a key {self.input_annotatable} in the "
                f"annotation context {context} is not an Annotabable.")

        return override


class AnnotatorBase(Annotator):
    """Base implementation of the `Annotator` class."""

    @abc.abstractmethod
    def _do_annotate(
        self, annotatable: Annotatable, context: dict
    ) -> dict:
        """Annotate the annotatable.

        Internal abstract method used for annotation. It should produce
        all source attributes defined for annotator.
        """

    def annotate(self, annotatable: Annotatable,
                 context: dict[str, Any]) -> dict[str, Any]:
        """Annotate and relabel attributes as configured.

        Uses `_do_annotate` to produce the annotation attributes.
        """
        annotatable_override = self._get_annotatable_override(
            annotatable, context)
        if annotatable_override is None:
            return self._empty_result()
        attributes = self._do_annotate(annotatable_override, context)
        return self._remap_annotation_attributes(attributes)
