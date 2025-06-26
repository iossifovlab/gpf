import abc
import itertools
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from dae.effect_annotation.effect import AlleleEffects
from dae.utils.regions import Region
from dae.variants.variant import SummaryAllele, SummaryVariant
from dae.variants_loaders.raw.loader import (
    FullVariant,
    VariantsGenotypesLoader,
)


class VariantsSource(abc.ABC):

    @abc.abstractmethod
    def fetch(self, region: Region | None = None) -> Iterable[FullVariant]:
        """Fetch variants."""


class VariantsConsumer(abc.ABC):
    """A terminator for variant processing pipelines."""

    @abc.abstractmethod
    def consume_one(self, full_variant: FullVariant) -> None:
        """Consume a single variant."""

    def consume(self, variants: Iterable[FullVariant]) -> None:
        """Consume variants."""
        for full_variant in variants:
            self.consume_one(full_variant)


class VariantsFilter(abc.ABC):
    """A filter that can be used to filter variants."""

    def filter(self, variants: Iterable[FullVariant]) -> Iterable[FullVariant]:
        """Filter variants."""
        for full_variant in variants:
            yield self.filter_one(full_variant)

    @abc.abstractmethod
    def filter_one(
        self, full_variant: FullVariant,
    ) -> FullVariant:
        """Filter a single variant."""


class VariantsBatchSource(abc.ABC):
    """A source that can fetch variants in batches."""

    @abc.abstractmethod
    def fetch_batches(
        self, region: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch variants in batches."""


class VariantsBatchConsumer(abc.ABC):
    """A sink that can write variants in batches."""

    @abc.abstractmethod
    def consume_batch(
        self, batch: Sequence[FullVariant],
    ) -> None:
        """Consume a single batch of variants."""

    def consume_batches(
        self, batches: Iterable[Sequence[FullVariant]],
    ) -> None:
        """Consume variants in batches."""
        for batch in batches:
            self.consume_batch(batch)


class VariantsBatchFilter(abc.ABC):
    """A filter that can filter variants in batches."""

    @abc.abstractmethod
    def filter_batch(
        self, batch: Sequence[FullVariant],
    ) -> Sequence[FullVariant]:
        """Filter variants in a single batch."""

    def filter_batches(
        self, batches: Iterable[Sequence[FullVariant]],
    ) -> Iterable[Sequence[FullVariant]]:
        """Filter variants in batches."""
        for batch in batches:
            yield self.filter_batch(batch)


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


class AnnotatablesFilter(abc.ABC):
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


class AnnotatablesBatchFilter(abc.ABC):
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


class AnnotationPipelineAnnotatablesFilter(AnnotatablesFilter):
    """A filter that can filter annotatables in batches."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        self.annotation_pipeline = annotation_pipeline

    def filter_one(
        self, annotatable: Annotatable | None,
    ) -> Annotation:
        """Filter annotatables."""
        annotations = self.annotation_pipeline.annotate(annotatable)
        return Annotation(annotatable=annotatable, annotations=annotations)


class AnnotationPipelineAnnotatablesBatchFilter(AnnotatablesBatchFilter):
    """A filter that can filter annotatables in batches."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        self.annotation_pipeline = annotation_pipeline

    def filter_batch(
        self, batch: Sequence[Annotatable | None],
    ) -> Sequence[Annotation]:
        """Filter annotatables in a single batch."""
        annotations = self.annotation_pipeline.batch_annotate(batch)
        return [
            Annotation(annotatable=annotatable, annotations=annotation)
            for annotatable, annotation in zip(batch, annotations, strict=True)
        ]


class AnnotationPipelineVariantsFilterMixin:
    """Mixin for annotation pipeline filters."""
    # pylint: disable=too-few-public-methods

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        self.annotation_pipeline = annotation_pipeline
        self._annotation_internal_attributes = {
            attribute.name
            for attribute in self.annotation_pipeline.get_attributes()
            if attribute.internal
        }

    def _apply_annotation_to_allele(
        self, summary_allele: SummaryAllele,
        annotation: Annotation,
    ) -> None:

        if "allele_effects" in annotation.annotations:
            allele_effects = annotation.annotations["allele_effects"]
            assert isinstance(allele_effects, AlleleEffects)
            # pylint: disable=protected-access
            summary_allele._effects = allele_effects  # noqa: SLF001
            del annotation.annotations["allele_effects"]
        public_attributes = {
            key: value for key, value in annotation.annotations.items()
            if key not in self._annotation_internal_attributes
        }
        summary_allele.update_attributes(public_attributes)


class AnnotationPipelineVariantsFilter(
        VariantsFilter, AnnotationPipelineVariantsFilterMixin):
    """Annotation pipeline batched variants filter."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        super().__init__(annotation_pipeline)
        self.annotatables_filter = AnnotationPipelineAnnotatablesFilter(
            annotation_pipeline)

    def filter_one(
        self, full_variant: FullVariant,
    ) -> FullVariant:
        annotatables = AnnotatablesWithContext(
            annotatables=[
                sa.get_annotatable()
                for sa in full_variant.summary_variant.alt_alleles],
            context=full_variant,
        )
        awc = self.annotatables_filter.filter_one_with_context(
                annotatables)

        full_variant = cast(FullVariant, awc.context)
        assert isinstance(full_variant.summary_variant, SummaryVariant)
        assert len(awc.annotations) == \
            len(full_variant.summary_variant.alt_alleles)
        for summary_allele, annotation in zip(
                full_variant.summary_variant.alt_alleles,
                awc.annotations, strict=True):
            assert isinstance(summary_allele, SummaryAllele)
            self._apply_annotation_to_allele(summary_allele, annotation)
        return full_variant


class AnnotationPipelineVariantsBatchFilter(
        VariantsBatchFilter, AnnotationPipelineVariantsFilterMixin):
    """Annotation pipeline batched variants filter."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        super().__init__(annotation_pipeline)
        self.annotatables_filter = AnnotationPipelineAnnotatablesBatchFilter(
            annotation_pipeline)

    def filter_batch(
        self, batch: Sequence[FullVariant],
    ) -> Sequence[FullVariant]:
        """Filter variants in batches."""
        annotatables_with_context = [
            AnnotatablesWithContext(
                annotatables=[
                    sa.get_annotatable()
                    for sa in v.summary_variant.alt_alleles],
                context=v,
            )
            for v in batch
        ]
        annotations_with_context = \
            self.annotatables_filter.filter_batch_with_context(
                annotatables_with_context)

        result: list[FullVariant] = []
        for awc in annotations_with_context:
            full_variant = cast(FullVariant, awc.context)
            assert isinstance(full_variant.summary_variant, SummaryVariant)
            assert len(awc.annotations) == \
                len(full_variant.summary_variant.alt_alleles)
            for summary_allele, annotation in zip(
                    full_variant.summary_variant.alt_alleles,
                    awc.annotations, strict=True):
                assert isinstance(summary_allele, SummaryAllele)
                self._apply_annotation_to_allele(summary_allele, annotation)

            result.append(full_variant)
        return result


class VariantsLoaderSource(VariantsSource):
    """A source that can fetch variants from a loader."""

    def __init__(self, loader: VariantsGenotypesLoader) -> None:
        self.loader = loader

    def fetch(self, region: Region | None = None) -> Iterable[FullVariant]:
        """Fetch full variants from a variant loader."""
        yield from self.loader.fetch(region)


class VariantsLoaderBatchSource(VariantsBatchSource):
    """A source that can fetch variants in batches from a loader."""

    def __init__(
        self, loader: VariantsGenotypesLoader,
        batch_size: int = 500,
    ) -> None:
        self.loader = loader
        self.batch_size = batch_size

    def fetch_batches(
        self, region: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch full variants from a variant loader in batches."""
        variants = self.loader.fetch(region)
        while batch := tuple(
                itertools.islice(variants, self.batch_size)):
            yield batch


class VariantsPipelineProcessor:
    """A processor that can be used to process variants in a pipeline."""

    def __init__(
        self,
        source: VariantsSource,
        filters: Sequence[VariantsFilter],
        sink: VariantsConsumer,
    ) -> None:
        self.source = source
        self.filters = filters
        self.sink = sink

    def process(self, region: Region | None = None) -> None:
        for full_variant in self.source.fetch(region):
            for variant_filter in self.filters:
                full_variant = variant_filter.filter_one(full_variant)
            self.sink.consume_one(full_variant)


class VariantsBatchPipelineProcessor:
    """A processor that can be used to process variants in a pipeline."""

    def __init__(
        self,
        source: VariantsBatchSource,
        filters: Sequence[VariantsBatchFilter],
        sink: VariantsBatchConsumer,
    ) -> None:
        self.source = source
        self.filters = filters
        self.sink = sink

    def process(self, region: Region | None = None) -> None:
        for batch in self.source.fetch_batches(region):
            for variant_filter in self.filters:
                batch = variant_filter.filter_batch(batch)
            self.sink.consume_batch(batch)
