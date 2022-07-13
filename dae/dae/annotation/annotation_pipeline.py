"""Provides annotation pipeline class."""

from __future__ import annotations

import logging

from typing import Dict, List, Optional

from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotator_base import Annotator
from dae.annotation.schema import Schema

logger = logging.getLogger(__name__)


class AnnotationPipeline():
    """Provides annotation pipeline abstraction."""

    def __init__(
            self, config: List[Dict],
            repository: GenomicResourceRepo):
        self.annotators: List[Annotator] = []
        self.config: List[Dict] = config
        self.repository: GenomicResourceRepo = repository

        self._annotation_schema: Optional[Schema] = None

    @property
    def annotation_schema(self) -> Schema:
        """Return annotation schema."""
        if self._annotation_schema is None:
            schema = Schema()
            for annotator in self.annotators:
                schema = Schema.concat_schemas(
                    schema, annotator.annotation_schema)
            self._annotation_schema = schema
        return self._annotation_schema

    def add_annotator(self, annotator: Annotator) -> None:
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)
        self._annotation_schema = None

    def annotate(self, annotatable: Annotatable) -> dict:
        context: dict = {}
        for annotator in self.annotators:
            attributes = annotator.annotate(annotatable, context)
            context.update(attributes)

        # TODO: Decide where context should be cleaned up
        # for annotator in self.annotators:
        #     for attr in annotator.get_annotation_config():
        #         if attr.get("internal", False):
        #             key = attr["destination"]
        #             del context[key]

        return context

    def close(self):
        for annotator in self.annotators:
            annotator.close()
