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
from dae.variants.variant import SummaryVariant
from dae.variants_loaders.raw.loader import FullVariant

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class AnnotatableWithContext:
    """The combination of an annotatable and its annotation."""
    annotatable: Annotatable | None
    annotation: dict[str, Any]


@dataclass(repr=True)
class AnnotatablesWithVariant:
    variant: SummaryVariant | FullVariant
    annotatables: list[Annotatable | None]


@dataclass(repr=True)
class AnnotatedVariant:
    """A variant and its annotatables with context."""
    variant: SummaryVariant | FullVariant
    awcs: list[AnnotatableWithContext]

    @property
    def annotatables(self) -> list[Annotatable | None]:
        return [awc.annotatable for awc in self.awcs]

    @property
    def annotations(self) -> list[dict[str, Any]]:
        return [awc.annotation for awc in self.awcs]


class AnnotatablesFilter(AbstractContextManager):
    """A filter that can filter annotatables."""

    @abc.abstractmethod
    def filter_one(
        self, annotatable: Annotatable | None,
    ) -> AnnotatableWithContext:
        """Filter a single annotatable."""

    def filter(
        self, annotatables: Iterable[Annotatable | None],
    ) -> Iterable[AnnotatableWithContext]:
        """Filter annotatables."""
        for annotatable in annotatables:
            yield self.filter_one(annotatable)

    def filter_one_with_context(
        self, annotatables: AnnotatablesWithVariant,
    ) -> AnnotatedVariant:
        return AnnotatedVariant(
            variant=annotatables.variant,
            awcs=list(self.filter(annotatables.annotatables)),
        )

    def filter_with_context(
        self, annotatables_with_context: Iterable[AnnotatablesWithVariant],
    ) -> Iterable[AnnotatedVariant]:
        """Filter annotatables with context."""
        for annotatables in annotatables_with_context:
            yield self.filter_one_with_context(annotatables)


class AnnotatablesBatchFilter(AbstractContextManager):
    """A filter that can filter annotatables in batches."""

    @abc.abstractmethod
    def filter_batch(
        self, batch: Sequence[Annotatable | None],
    ) -> Sequence[AnnotatableWithContext]:
        """Filter annotatables in a single batch."""

    def filter_batches(
        self, batches: Iterable[Sequence[Annotatable | None]],
    ) -> Iterable[Sequence[AnnotatableWithContext]]:
        """Filter annotatables in batches."""
        for batch in batches:
            annotations = list(self.filter_batch(batch))
            yield annotations

    def filter_batch_with_context(
        self,
        batch_with_context: Sequence[AnnotatablesWithVariant],
    ) -> Sequence[AnnotatedVariant]:
        """Filter a single batch of annotatables with context."""
        annotatables_batch = list(itertools.chain.from_iterable(
            awc.annotatables for awc in batch_with_context
        ))
        annotations = self.filter_batch(annotatables_batch)
        assert len(annotations) == len(annotatables_batch)

        annotations_iter = iter(annotations)
        result: list[AnnotatedVariant] = []
        for awc in batch_with_context:
            # pylint: disable=stop-iteration-return
            awcs: list[AnnotatableWithContext] = [
                next(annotations_iter)
                for _ in awc.annotatables
            ]
            result.append(
                AnnotatedVariant(variant=awc.variant, awcs=awcs),
            )

        return result

    def filter_batches_with_context(
        self,
        batches_with_context: Iterable[Sequence[AnnotatablesWithVariant]],
    ) -> Iterable[Sequence[AnnotatedVariant]]:
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
        exc_tb: TracebackType | None,
    ) -> bool:
        self.annotation_pipeline.close()
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        return exc_type is not None


class AnnotateFilter(
    AnnotatablesFilter,
    AnnotationPipelineContextManager,
):
    """A filter that annotates a single annotatable."""
    def filter_one(
        self, annotatable: Annotatable | None,
    ) -> AnnotatableWithContext:
        """Filter annotatables."""
        annotation = self.annotation_pipeline.annotate(annotatable)
        return AnnotatableWithContext(annotatable=annotatable,
                                      annotation=annotation)


class AnnotateBatchFilter(
    AnnotatablesBatchFilter,
    AnnotationPipelineContextManager,
):
    """A filter that annotates in batches."""
    def filter_batch(
        self, batch: Sequence[Annotatable | None],
    ) -> Sequence[AnnotatableWithContext]:
        """Filter annotatables in a single batch."""
        annotation = self.annotation_pipeline.batch_annotate(batch)
        return [
            AnnotatableWithContext(annotatable=annotatable,
                                   annotation=annotation)
            for annotatable, annotation in zip(batch, annotation, strict=True)
        ]
