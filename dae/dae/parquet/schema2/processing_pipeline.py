import abc
import itertools
from collections.abc import Generator, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from dae.utils.regions import Region
from dae.variants_loaders.raw.loader import FullVariant


class PipelineProcessor(abc.ABC):
    """A processor that can be used to process variants in a pipeline."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        self.annotation_pipeline = annotation_pipeline

    @abc.abstractmethod
    def process(self, variants: Iterable[FullVariant]) -> None:
        """Process a single variant."""


class VariantsSource(abc.ABC):

    @abc.abstractmethod
    def fetch(self, region: Region | None = None) -> Iterable[FullVariant]:
        """Fetch variants."""


class VariantsSink(abc.ABC):

    @abc.abstractmethod
    def write(self, variants: Iterable[FullVariant]) -> None:
        """Write variants to the sink."""


class VariantsFilter(abc.ABC):
    """A filter that can be used to filter variants."""

    @abc.abstractmethod
    def filter(self, variants: Iterable[FullVariant]) -> Iterable[FullVariant]:
        """Filter variants."""


class AnnotationPipelineFilter(VariantsFilter):
    """A filter that uses an annotation pipeline to filter variants."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        self.annotation_pipeline = annotation_pipeline

    def filter(
        self, variants: Iterable[FullVariant],
    ) -> Generator[FullVariant, None, None]:
        """Filter variants using the annotation pipeline."""
        yield from variants


class VariantsBatchSource(VariantsSource):
    """A source that can fetch variants in batches."""

    @abc.abstractmethod
    def fetch_batches(
        self, region: Region | None = None,
    ) -> Iterable[Iterable[FullVariant]]:
        """Fetch variants in batches."""


class VariantsBatchSink(VariantsSink):
    """A sink that can write variants in batches."""

    @abc.abstractmethod
    def write_batches(self, batches: Iterable[Iterable[FullVariant]]) -> None:
        """Write variants in batches."""


class VariantsBatchFilter(VariantsFilter):
    """A filter that can filter variants in batches."""

    @abc.abstractmethod
    def filter_batches(
        self, batches: Iterable[Iterable[FullVariant]],
    ) -> Iterable[Iterable[FullVariant]]:
        """Filter variants in batches."""


@dataclass(repr=True)
class Annotation:
    """An annotatable with annotations."""

    annotatable: Annotatable
    annotations: dict[str, Any]


@dataclass(repr=True)
class AnnotatablesWithContext:

    annotatables: list[Annotatable]
    context: Any


@dataclass
class AnnotationsWithContext:

    annotations: list[Annotation]
    context: Any


class AnnotatablesFilter(abc.ABC):
    """A filter that can filter annotatables."""

    @abc.abstractmethod
    def filter(
        self, annotatables: Iterable[Annotatable],
    ) -> Iterable[Annotation]:
        """Filter annotatables."""

    def filter_with_context(
        self, annotatables_with_context: Iterable[AnnotatablesWithContext],
    ) -> Iterable[AnnotationsWithContext]:
        """Filter annotatables with context."""
        for annotatables in annotatables_with_context:
            annotations = list(self.filter(annotatables.annotatables))
            yield AnnotationsWithContext(
                annotations=annotations,
                context=annotatables.context,
            )


class AnnotatablesBatchFilter(abc.ABC):
    """A filter that can filter annotatables in batches."""

    @abc.abstractmethod
    def filter_batch(
        self, batch: Iterable[Annotatable],
    ) -> Sequence[Annotation]:
        """Filter annotatables in a single batch."""

    def filter_batches(
        self, batches: Iterable[Sequence[Annotatable]],
    ) -> Iterable[Sequence[Annotation]]:
        """Filter annotatables in batches."""
        for batch in batches:
            annotations = list(self.filter_batch(batch))
            yield annotations

    def filter_batches_with_context(
        self,
        batches_with_context: Iterable[Sequence[AnnotatablesWithContext]],
    ) -> Iterable[list[AnnotationsWithContext]]:
        """Filter annotatables with context in batches."""

        for batch_with_context in batches_with_context:
            annotatables_batch = list(itertools.chain.from_iterable(
                awc.annotatables for awc in batch_with_context
            ))
            annotations = self.filter_batch(annotatables_batch)
            assert len(annotations) == len(annotatables_batch)

            annotations_iter = iter(annotations)
            result: list[AnnotationsWithContext] = []
            for awc in batch_with_context:
                annos: list[Annotation] = [
                    next(annotations_iter)
                    for _ in range(len(awc.annotatables))
                ]
                result.append(
                    AnnotationsWithContext(
                        annotations=annos, context=awc.context))
            yield result
