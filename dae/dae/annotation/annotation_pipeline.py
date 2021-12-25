from __future__ import annotations

import logging

from typing import Dict, List, Optional

from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotator_base import Annotator
from dae.annotation.schema import Schema
from dae.annotation.annotation_context import AnnotationPipelineContext

logger = logging.getLogger(__name__)


class AnnotationPipeline():
    def __init__(
            self, config: List[Dict],
            repository: GenomicResourceRepo,
            context: Optional[AnnotationPipelineContext]):
        self.annotators: List[Annotator] = []
        self.config: List[Dict] = config
        self.repository: GenomicResourceRepo = repository
        self.context: Optional[AnnotationPipelineContext] = context

        self._annotation_schema = None

    @ property
    def annotation_schema(self) -> Schema:
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
        context = {}
        for annotator in self.annotators:
            attributes = annotator.annotate(annotatable, context)
            context.update(attributes)

        return context
