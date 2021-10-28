import logging
import abc

import pyarrow as pa
from typing import List, Optional

from dae.variants.core import Allele

logger = logging.getLogger(__name__)


class Annotator(abc.ABC):

    TYPES = {
        "float": pa.float32(),
        "integer": pa.int32(),
        "string": pa.string(),
    }

    def __init__(self, liftover: str = None, override: dict = None):
        self.liftover = liftover
        self.override = override

    @staticmethod
    def required_columns():
        raise NotImplementedError()

    @property
    def output_columns(self) -> List[str]:
        return self.annotation_schema.names

    @abc.abstractproperty
    def annotation_schema(self):
        pass

    @abc.abstractmethod
    def _do_annotate_allele(
            self, attributes: dict,
            allele: Allele,
            liftover_context: Optional[dict]):
        """
        Internal abstract method used for annotation.
        """
        pass

    @abc.abstractmethod
    def get_default_annotation(self):
        pass

    def annotate_allele(
            self, attributes: dict,
            allele: Allele,
            liftover_context: Optional[dict]):
        """
        Carry out the annotation and then relabel results as configured.
        """
        self._do_annotate_allele(attributes, allele, liftover_context)
        attributes_list = self.get_default_annotation()
        for attr in attributes_list:
            if attr.dest == attr.source:
                continue
            attributes[attr.dest] = attributes[attr.source]
            del attributes[attr.source]
