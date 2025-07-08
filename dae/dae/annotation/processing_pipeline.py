from __future__ import annotations

import abc
import itertools
import logging
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class Annotation:
    annotatable: Annotatable | None = field()
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnnotationsWithSource:
    source: Any
    annotations: list[Annotation]


class AnnotatablesFilter(AbstractContextManager):
    """A filter that can filter annotatables."""

    @abc.abstractmethod
    def filter_one(
        self, annotation: Annotation,
    ) -> Annotation:
        """Filter a single annotatable."""

    def filter(
        self, data: Iterable[Annotation],
    ) -> Iterable[Annotation]:
        """Filter a single batch of annotatables."""
        for annotation in data:
            yield self.filter_one(annotation)

    def filter_one_with_source(
        self, data: AnnotationsWithSource,
    ) -> AnnotationsWithSource:
        new_annotations = list(self.filter(data.annotations))
        return AnnotationsWithSource(
            annotations=new_annotations,
            source=data.source,
        )

    def filter_with_source(
        self, data: Iterable[AnnotationsWithSource],
    ) -> Iterable[AnnotationsWithSource]:
        """Filter annotatables with source."""
        for annotations_with_source in data:
            yield self.filter_one_with_source(annotations_with_source)


class AnnotatablesBatchFilter(AbstractContextManager):
    """A filter that can filter annotatables in batches."""

    @abc.abstractmethod
    def filter_batch(
        self, batch: Sequence[Annotation],
    ) -> Sequence[Annotation]:
        """Filter annotatables in a single batch."""

    def filter_batches(
        self, batches: Iterable[Sequence[Annotation]],
    ) -> Iterable[Sequence[Annotation]]:
        """Filter annotatables in batches."""
        for batch in batches:
            annotations = list(self.filter_batch(batch))
            yield annotations

    def filter_batch_with_source(
        self,
        batch_with_source: Sequence[AnnotationsWithSource],
    ) -> Sequence[AnnotationsWithSource]:
        """Filter a single batch of annotatables with source."""
        annotations_batch = list(itertools.chain.from_iterable(
            aws.annotations for aws in batch_with_source
        ))
        new_annotations = self.filter_batch(annotations_batch)
        assert len(new_annotations) == len(annotations_batch)

        annotations_iter = iter(new_annotations)
        result: list[AnnotationsWithSource] = []
        for aws in batch_with_source:
            # pylint: disable=stop-iteration-return
            annos: list[Annotation] = [
                next(annotations_iter)
                for _ in aws.annotations
            ]
            result.append(
                AnnotationsWithSource(
                    annotations=annos, source=aws.source))

        return result

    def filter_batches_with_source(
        self,
        batches_with_source: Iterable[Sequence[AnnotationsWithSource]],
    ) -> Iterable[Sequence[AnnotationsWithSource]]:
        """Filter annotatables with source in batches."""
        for batch_with_source in batches_with_source:
            yield self.filter_batch_with_source(batch_with_source)


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
        self, annotation: Annotation,
    ) -> Annotation:
        """Filter annotatables."""
        result = self.annotation_pipeline.annotate(
            annotation.annotatable, context=annotation.context)
        return Annotation(annotatable=annotation.annotatable, context=result)


class AnnotationPipelineAnnotatablesBatchFilter(
        AnnotatablesBatchFilter, AnnotationPipelineContextManager):
    """A filter that can filter annotatables in batches."""

    def filter_batch(
        self, batch: Sequence[Annotation],
    ) -> Sequence[Annotation]:
        """Filter annotatables in a single batch."""
        annotatable_batch, context_batch = [], []
        for annotation in batch:
            annotatable_batch.append(annotation.annotatable)
            context_batch.append(annotation.context)

        annotations = self.annotation_pipeline.batch_annotate(
            annotatable_batch, contexts=context_batch)
        return [
            Annotation(annotatable=annotatable, context=annotation)
            for annotatable, annotation in zip(annotatable_batch, annotations,
                                               strict=True)
        ]
