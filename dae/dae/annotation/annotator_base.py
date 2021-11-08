import logging
import abc

from typing import List, Optional

from .annotatable import Annotatable
from .schema import Schema

logger = logging.getLogger(__name__)


class Annotator(abc.ABC):

    def __init__(self, liftover: str = None, override: dict = None):
        self.liftover = liftover
        self.override = override

    @property
    def output_columns(self) -> List[str]:
        return self.annotation_schema.names

    @abc.abstractproperty
    def annotation_schema(self) -> Schema:
        pass

    @abc.abstractproperty
    def annotator_type(self) -> str:
        pass

    @abc.abstractmethod
    def _do_annotate(
            self, attributes: dict,
            allele: Annotatable,
            liftover_context: Optional[dict]):
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
            liftover_context: Optional[dict]):
        """
        Carry out the annotation and then relabel results as configured.
        """
        self._do_annotate(attributes, annotatable, liftover_context)
        attributes_list = self.get_annotation_config()
        for attr in attributes_list:
            if attr.dest == attr.source:
                continue
            attributes[attr.dest] = attributes[attr.source]
            del attributes[attr.source]
