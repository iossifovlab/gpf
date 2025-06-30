from __future__ import annotations

import abc
import itertools
import logging
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from types import TracebackType
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class Annotation:
    """An annotatable with annotations."""

    annotatable: Annotatable | None
    annotations: dict[str, Any]


@dataclass(repr=True)
class AnnotatablesWithContext:

    annotatables: list[Annotatable | None]
    context: Any


@dataclass
class AnnotationsWithContext:

    annotations: list[Annotation]
    context: Any


class AnnotatablesFilter(AbstractContextManager):
    """A filter that can filter annotatables."""

    @abc.abstractmethod
    def filter_one(
        self, annotatable: Annotatable | None,
    ) -> Annotation:
        """Filter a single annotatable."""

    def filter(
        self, annotatables: Iterable[Annotatable | None],
    ) -> Iterable[Annotation]:
        """Filter annotatables."""
        for annotatable in annotatables:
            yield self.filter_one(annotatable)

    def filter_one_with_context(
        self, annotatables: AnnotatablesWithContext,
    ) -> AnnotationsWithContext:
        annotations = list(self.filter(annotatables.annotatables))
        return AnnotationsWithContext(
            annotations=annotations,
            context=annotatables.context,
        )

    def filter_with_context(
        self, annotatables_with_context: Iterable[AnnotatablesWithContext],
    ) -> Iterable[AnnotationsWithContext]:
        """Filter annotatables with context."""
        for annotatables in annotatables_with_context:
            yield self.filter_one_with_context(annotatables)


class AnnotatablesBatchFilter(AbstractContextManager):
    """A filter that can filter annotatables in batches."""

    @abc.abstractmethod
    def filter_batch(
        self, batch: Sequence[Annotatable | None],
    ) -> Sequence[Annotation]:
        """Filter annotatables in a single batch."""

    def filter_batches(
        self, batches: Iterable[Sequence[Annotatable | None]],
    ) -> Iterable[Sequence[Annotation]]:
        """Filter annotatables in batches."""
        for batch in batches:
            annotations = list(self.filter_batch(batch))
            yield annotations

    def filter_batch_with_context(
        self,
        batch_with_context: Sequence[AnnotatablesWithContext],
    ) -> Sequence[AnnotationsWithContext]:
        """Filter a single batch of annotatables with context."""
        annotatables_batch = list(itertools.chain.from_iterable(
            awc.annotatables for awc in batch_with_context
        ))
        annotations = self.filter_batch(annotatables_batch)
        assert len(annotations) == len(annotatables_batch)

        annotations_iter = iter(annotations)
        result: list[AnnotationsWithContext] = []
        for awc in batch_with_context:
            # pylint: disable=stop-iteration-return
            annos: list[Annotation] = [
                next(annotations_iter)
                for _ in awc.annotatables
            ]
            result.append(
                AnnotationsWithContext(
                    annotations=annos, context=awc.context))

        return result

    def filter_batches_with_context(
        self,
        batches_with_context: Iterable[Sequence[AnnotatablesWithContext]],
    ) -> Iterable[Sequence[AnnotationsWithContext]]:
        """Filter annotatables with context in batches."""
        for batch_with_context in batches_with_context:
            yield self.filter_batch_with_context(batch_with_context)


class AnnotationPipelineContextManager(AbstractContextManager):
    """A context manager for annotation pipelines."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        self.annotation_pipeline = annotation_pipeline

    def __enter__(self) -> AnnotationPipelineContextManager:
        """Enter the context manager."""
        self.annotation_pipeline.open()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        self.annotation_pipeline.close()
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        return exc_type is not None


class AnnotationPipelineAnnotatablesFilter(
        AnnotatablesFilter, AnnotationPipelineContextManager):
    """A filter that can filter annotatables in batches."""

    def filter_one(
        self, annotatable: Annotatable | None,
    ) -> Annotation:
        """Filter annotatables."""
        annotations = self.annotation_pipeline.annotate(annotatable)
        return Annotation(annotatable=annotatable, annotations=annotations)


class AnnotationPipelineAnnotatablesBatchFilter(
        AnnotatablesBatchFilter, AnnotationPipelineContextManager):
    """A filter that can filter annotatables in batches."""

    def filter_batch(
        self, batch: Sequence[Annotatable | None],
    ) -> Sequence[Annotation]:
        """Filter annotatables in a single batch."""
        annotations = self.annotation_pipeline.batch_annotate(batch)
        return [
            Annotation(annotatable=annotatable, annotations=annotation)
            for annotatable, annotation in zip(batch, annotations, strict=True)
        ]
