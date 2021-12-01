import logging
import abc

from typing import List, Optional, Dict
from box import Box
from cerberus.validator import Validator

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
    '''
    Annotator provides a set of attrubutes for a given Annotatable.
    '''

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

    def __init__(self, config: Box):
        self.config = self.validate_config(config)
        self.input_annotatable = self.config.get("input_annotatable")

    @abc.abstractclassmethod
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

    @abc.abstractproperty
    def annotation_schema(self) -> Schema:
        pass

    @abc.abstractstaticmethod
    def annotator_type() -> str:
        pass

    @abc.abstractmethod
    def _do_annotate(
            self, allele: Annotatable, context: Optional[dict]) -> Dict:
        """
        Internal abstract method used for annotation.
        """
        pass

    @abc.abstractmethod
    def get_annotation_config(self):
        pass

    def annotate(
            self, annotatable: Annotatable, context: Optional[dict]) -> Dict:
        """
        Carry out the annotation and then relabel resulting attributes
        as configured.
        """
        if self.input_annotatable is not None:
            annotatable = context.get(self.input_annotatable)
            if annotatable is None:
                logger.info(
                    f"can't find input annotatable {self.input_annotatable} "
                    f"in annotation context: {context}")
                return {}

        attributes = self._do_annotate(annotatable, context)
        attributes_list = self.get_annotation_config()
        for attr in attributes_list:
            if attr.destination == attr.source:
                continue
            attributes[attr.destination] = attributes[attr.source]
            del attributes[attr.source]

        return attributes
