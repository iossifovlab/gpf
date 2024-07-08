"""Provides base class for annotators."""
from __future__ import annotations

import abc
import os
from itertools import starmap
from pathlib import Path
from typing import Any, cast

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

        self.work_dir: Path = cast(Path, info.parameters.get("work_dir"))
        if self.work_dir is not None:
            os.makedirs(self.work_dir, exist_ok=True)

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

    def _do_batch_annotate(
        self, annotatables: list[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """
        Annotate a batch of annotatables.

        Internal abstract method used for batch annotation.
        """
        return list(starmap(
            self.annotate, zip(annotatables, contexts, strict=True),
        ))

    def batch_annotate(
        self, annotatables: list[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        inner_output = self._do_batch_annotate(
            annotatables, contexts, batch_work_dir=batch_work_dir,
        )
        return [{
            attr.name: result[attr.source]
            for attr in self._info.attributes
        } for result in inner_output]
