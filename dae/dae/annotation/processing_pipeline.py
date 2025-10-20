from __future__ import annotations

import abc
import itertools
import logging
from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from dae.utils.processing_pipeline import Filter

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class Annotation:
    """
    A pair of an annotatable and its relevant context.

    The context can hold any key/value pair relevant to the
    annotatable and is typically used to store the results of
    annotators.
    """
    annotatable: Annotatable | None = field()
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnnotationsWithSource:
    """
    A pair of a list of Annotation instances and their source.

    The source is typically a variant read from some format, with
    the 'annotations' attribute corresponding to its alleles.
    """
    source: Any
    annotations: list[Annotation]


class AnnotationsWithSourceFilter(Filter):
    """Base class for filters that work on AnnotationsWithSource objects."""

    @abc.abstractmethod
    def _filter_annotation(
        self, annotation: Annotation,
    ) -> Annotation:
        ...

    def filter(
        self, data: AnnotationsWithSource,
    ) -> AnnotationsWithSource:
        """Filter a single AnnotationsWithSource object."""
        new_annotations = [self._filter_annotation(annotation)
                           for annotation in data.annotations]
        return AnnotationsWithSource(
            annotations=new_annotations,
            source=data.source,
        )


class AnnotationsWithSourceBatchFilter(Filter):
    """Base class for filters that work on AnnotationsWithSource batches."""

    @abc.abstractmethod
    def _filter_annotation_batch(
        self, batch: Sequence[Annotation],
    ) -> Sequence[Annotation]:
        ...

    def filter(
        self, data: Sequence[AnnotationsWithSource],
    ) -> Sequence[AnnotationsWithSource]:
        """Filter a batch of AnnotationsWithSource objects."""
        annotations_batch = list(itertools.chain.from_iterable(
            aws.annotations for aws in data
        ))
        new_annotations = self._filter_annotation_batch(annotations_batch)
        assert len(new_annotations) == len(annotations_batch)

        annotations_iter = iter(new_annotations)
        result: list[AnnotationsWithSource] = []
        for aws in data:
            # pylint: disable=stop-iteration-return
            annos: list[Annotation] = [
                next(annotations_iter)
                for _ in aws.annotations
            ]
            result.append(
                AnnotationsWithSource(annotations=annos, source=aws.source))

        return result


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
        exc_tb: TracebackType | None,
    ) -> bool:
        self.annotation_pipeline.close()
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        return exc_type is None


class AnnotationPipelineAnnotatablesFilter(
    AnnotationsWithSourceFilter,
    AnnotationPipelineContextManager,
):
    """
    Filter that annotates an AnnotationWithSource object using a pipeline.
    """
    def _filter_annotation(
        self, annotation: Annotation,
    ) -> Annotation:
        result = self.annotation_pipeline.annotate(
            annotation.annotatable, context=annotation.context)
        return Annotation(annotatable=annotation.annotatable, context=result)


class AnnotationPipelineAnnotatablesBatchFilter(
    AnnotationsWithSourceBatchFilter,
    AnnotationPipelineContextManager,
):
    """
    Filter that annotates an AnnotationWithSource batch using a pipeline.
    """

    def _filter_annotation_batch(
        self, batch: Sequence[Annotation],
    ) -> Sequence[Annotation]:
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


class DeleteAttributesFromAWSFilter(Filter):
    """Filter to remove items from AWSs. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self.to_remove = set(attributes_to_remove)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is None

    def filter(self, data: AnnotationsWithSource) -> AnnotationsWithSource:
        for attr in self.to_remove:
            if attr in data.source:
                del data.source[attr]
        return data


class DeleteAttributesFromAWSBatchFilter(Filter):
    """Filter to remove items from AWS batches. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self._delete_filter = DeleteAttributesFromAWSFilter(
            attributes_to_remove)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is None

    def filter(
        self, data: Sequence[AnnotationsWithSource],
    ) -> Sequence[AnnotationsWithSource]:
        for aws in data:
            self._delete_filter.filter(aws)
        return data
