"""Provides base class for annotators."""
from __future__ import annotations

import abc
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotatorInfo
from dae.annotation.annotation_pipeline import AnnotationPipeline, Annotator


class AnnotatorBase(Annotator):
    """Base implementation of the `Annotator` class."""

    def __init__(self, pipeline: AnnotationPipeline | None,
                 info: AnnotatorInfo,
                 source_type_desc: dict[str, tuple[str, str]]):
        for attribute_config in info.attributes:
            if attribute_config.source not in source_type_desc:
                raise ValueError(f"The source {attribute_config.source} "
                                 " is not supported for the annotator "
                                 f"{info.type}")
            att_type, att_desc = source_type_desc[attribute_config.source]
            attribute_config.type = att_type
            attribute_config.description = att_desc
        super().__init__(pipeline, info)

    @abc.abstractmethod
    def _do_annotate(self, annotatable: Annotatable, context: dict[str, Any]) \
            -> dict[str, Any]:
        """Annotate the annotatable.

        Internal abstract method used for annotation. It should produce
        all source attributes defined for annotator.
        """

    def annotate(
        self, annotatable: Annotatable | None, context: dict[str, Any],
    ) -> dict[str, Any]:
        if annotatable is None:
            return self._empty_result()
        source_values = self._do_annotate(annotatable, context)
        return {attribute_config.name: source_values[attribute_config.source]
                for attribute_config in self._info.attributes}
