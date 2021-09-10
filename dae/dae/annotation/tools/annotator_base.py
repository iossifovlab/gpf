import logging
import abc

import pyarrow as pa
from typing import List

logger = logging.getLogger(__name__)


class Annotator(abc.ABC):

    TYPES = {
        "float": pa.float32(),
        "integer": pa.int32(),
        "string": pa.string(),
    }

    def __init__(self, liftover=None, override=None):
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

    def _do_annotate(self, attributes, variant, liftover_variants):
        """
        Internal abstract method used for annotation.
        """
        raise NotImplementedError()

    def get_default_annotation(self):
        raise NotImplementedError()

    def annotate(self, attributes, variant, liftover_variants):
        """
        Carry out the annotation and then relabel results as configured.
        """
        self._do_annotate(attributes, variant, liftover_variants)
        attributes_list = self.get_default_annotation()
        print("attributes_list:", attributes_list)
        for attr in attributes_list:
            if attr.dest == attr.source:
                continue
            attributes[attr.dest] = attributes[attr.source]
            del attributes[attr.source]
