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
from dae.variants_loaders.raw.loader import FullVariant

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class AnnotatableWithContext:
    annotatable: Annotatable | None = field()
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class VariantWithAWCs:
    variant: FullVariant
    awcs: list[AnnotatableWithContext]


class AnnotatablesFilter(AbstractContextManager):
    """A filter that can filter annotatables."""

    @abc.abstractmethod
    def filter_awc(
        self, awc: AnnotatableWithContext,
    ) -> AnnotatableWithContext:
        """Filter a single annotatable."""

    def filter(self, variant: VariantWithAWCs) -> VariantWithAWCs:
        filtered_awcs = [
            self.filter_awc(awc)
            for awc in variant.awcs
        ]
        return VariantWithAWCs(
            variant=variant.variant,
            awcs=filtered_awcs,
        )


class AnnotatablesBatchFilter(AbstractContextManager):
    """A filter that can filter annotatables in batches."""

    @abc.abstractmethod
    def filter_awc_batch(
        self, batch: Sequence[AnnotatableWithContext],
    ) -> Sequence[AnnotatableWithContext]:
        """Filter annotatables in a single batch."""

    def filter_batch(
        self, batch: Sequence[VariantWithAWCs],
    ) -> Sequence[VariantWithAWCs]:
        """Filter a single batch of annotatables with context."""
        annotatables_batch = list(itertools.chain.from_iterable(
            variant.awcs for variant in batch
        ))
        annotations = self.filter_awc_batch(annotatables_batch)
        assert len(annotations) == len(annotatables_batch)

        annotations_iter = iter(annotations)
        result: list[VariantWithAWCs] = []
        for variant in batch:
            # pylint: disable=stop-iteration-return
            annos: list[AnnotatableWithContext] = [
                next(annotations_iter)
                for _ in variant.awcs
            ]
            result.append(VariantWithAWCs(variant=variant.variant, awcs=annos))

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

    def filter_awc(
        self, awc: AnnotatableWithContext,
    ) -> AnnotatableWithContext:
        """Filter annotatables."""
        annotations = self.annotation_pipeline.annotate(
            awc.annotatable, context=awc.context)
        return AnnotatableWithContext(annotatable=awc.annotatable,
                                      context=annotations)


class AnnotationPipelineAnnotatablesBatchFilter(
        AnnotatablesBatchFilter, AnnotationPipelineContextManager):
    """A filter that can filter annotatables in batches."""

    def filter_awc_batch(
        self, batch: Sequence[AnnotatableWithContext],
    ) -> Sequence[AnnotatableWithContext]:
        """Filter annotatables in a single batch."""
        annotatable_batch, context_batch = [], []
        for awc in batch:
            annotatable_batch.append(awc.annotatable)
            context_batch.append(awc.context)

        annotations = self.annotation_pipeline.batch_annotate(
            annotatable_batch, contexts=context_batch)
        return [
            AnnotatableWithContext(annotatable=annotatable, context=annotation)
            for annotatable, annotation in zip(annotatable_batch, annotations,
                                               strict=True)
        ]
