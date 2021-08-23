import logging
from copy import deepcopy
from dae.configuration.schemas.genomic_resources_database import attr_schema, \
    genomic_score_schema

logger = logging.getLogger(__name__)


class Annotator:

    def __init__(self, resource, liftover=None, override=None):
        self.resource = resource
        self.config = override if override \
            else resource.get_default_annotation()

        # FIXME Reintroduce Graw, Traw and TrawFormat?

        self.liftover = liftover
        self.override = override

    @staticmethod
    def required_columns():
        raise NotImplementedError()

    @property
    def output_columns(self):
        raise NotImplementedError()

    @classmethod
    def get_config_schema(cls):
        attributes_schemas = {
            attr_name: attr_schema for attr_name in cls.required_columns()
        }
        schema = deepcopy(genomic_score_schema)
        schema.update(attributes_schemas)
        return schema

    def _do_annotate(self, attributes, variant, liftover_variants):
        """
        Internal abstract method used for annotation.
        """
        raise NotImplementedError()

    def annotate(self, attributes, variant, liftover_variants):
        """
        Carry out the annotation and then relabel results as configured.
        """
        self._do_annotate(attributes, variant, liftover_variants)
        attributes_list = self.resource._config.default_annotation.attributes
        if self.override is not None:
            attributes_list = self.override.attributes
        for attr in attributes_list:
            if attr.dest == attr.source:
                continue
            attributes[attr.dest] = attributes[attr.source]
            del attributes[attr.source]
