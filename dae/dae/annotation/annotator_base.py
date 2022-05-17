import logging
import abc

from typing import Any, List, Dict
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

    def __init__(self, config: dict):
        self.config = self.validate_config(config)
        self.input_annotatable = self.config.get("input_annotatable")
        self._annotation_schema = None

    @classmethod
    @abc.abstractmethod
    def validate_config(cls, config: Dict) -> Dict:
        """
        Normalizes and validates the annotation configuration.

        When validation passes returns the normalized and validated
        annotator configuration dict.

        When validation fails, raises ValueError.
        """
        return config

    @abc.abstractmethod
    def get_all_annotation_attributes(self) -> List[Dict]:
        """
        Returns list of all available attributes that could be provided by
        the annotator.

        The result is a list of dicts. Each dict contains following
        attributes:

        * source: the name of the attribute
        * type: type of the attribute
        * desc: descripion of the attribute

        """
        return []

    def get_annotation_attribute(self, attribute_name) -> Dict[str, str]:
        for attribute in self.get_all_annotation_attributes():
            if attribute_name == attribute["name"]:
                return attribute
        message = f"can't find attribute {attribute_name} in annotator " \
            f"{self.annotator_type()}: {self.config}"
        logger.error(message)
        raise ValueError(message)

    @property
    def annotation_schema(self):
        if self._annotation_schema is None:
            schema = Schema()
            for attribute in self.get_annotation_config():
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
        """Returns annotator type."""

    @abc.abstractmethod
    def _do_annotate(
            self, annotatable: Annotatable, context: Dict) -> Dict:
        """
        Internal abstract method used for annotation.
        """

    @abc.abstractmethod
    def get_annotation_config(self) -> List[Dict]:
        """Returns annotation config."""

    def _empty_result(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for attr in self.get_annotation_config():
            result[attr["destination"]] = None
        return result

    def annotate(self, annotatable: Annotatable,
                 context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Carry out the annotation and then relabel resulting attributes
        as configured.
        """
        if self.input_annotatable is not None:
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
                return self._empty_result()

            if not isinstance(override, Annotatable):
                raise ValueError(
                    f"The object with a key {self.input_annotatable} in the "
                    f"annotation context {context} is not an Annotabable.")

            annotatable = override

        attributes = self._do_annotate(annotatable, context)
        attributes_list = self.get_annotation_config()
        for attr in attributes_list:
            if attr["destination"] == attr["source"]:
                continue
            attributes[attr["destination"]] = attributes[attr["source"]]
            del attributes[attr["source"]]

        return attributes
