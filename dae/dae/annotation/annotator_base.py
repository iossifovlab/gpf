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

    # def __init__(self, pipeline: AnnotationPipeine, configuation: dict):
    #    self.liftover = config.get("liftover", None)

    # def annnotate(annotatable, context, )
    #   returns a dictionary where the keys are based on the 'distination'.

    # def get_possible_source_attributes():
    #     returns a list of the ('source', type, description)

    def __init__(self, config: Box):
        self.validate_config(config)
        self.config = config
        self.id = self.config.get("id")

    @abc.abstractclassmethod
    def validate_config(cls, config: Dict) -> Dict:
        """
        Normalizes and validates the annotation configuration.

        When validation passes returns the normalized and validated
        annotator configuration dict.

        When validation fails, raises ValueError.
        """
        return config

    @property
    def output_columns(self) -> List[str]:
        return self.annotation_schema.names

    @abc.abstractproperty
    def annotation_schema(self) -> Schema:
        pass

    @abc.abstractstaticmethod
    def annotator_type() -> str:
        pass

    @abc.abstractmethod
    def _do_annotate(
            self, attributes: dict,
            allele: Annotatable,
            context: Optional[dict]):
        """
        Internal abstract method used for annotation.
        """
        pass

    @abc.abstractmethod
    def get_annotation_config(self):
        pass

    def annotate(
            self, attributes: dict,
            annotatable: Annotatable,
            context: Optional[dict]):
        """
        Carry out the annotation and then relabel resulting attributes
        as configured.
        """
        self._do_annotate(attributes, annotatable, context)
        attributes_list = self.get_annotation_config()
        for attr in attributes_list:
            if attr.destination == attr.source:
                continue
            attributes[attr.destination] = attributes[attr.source]
            del attributes[attr.source]
