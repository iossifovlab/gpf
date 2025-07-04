from __future__ import annotations

import abc
import itertools
import logging
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from types import TracebackType
from typing import cast

from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from dae.annotation.processing_pipeline import (
    AnnotatablesWithContext,
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
)
from dae.effect_annotation.effect import AlleleEffects
from dae.utils.regions import Region
from dae.variants.variant import SummaryAllele, SummaryVariant
from dae.variants_loaders.raw.loader import (
    FullVariant,
    VariantsGenotypesLoader,
)

logger = logging.getLogger(__name__)


class VariantsSource(AbstractContextManager):

    @abc.abstractmethod
    def fetch(self, region: Region | None = None) -> Iterable[FullVariant]:
        """Fetch variants."""


class VariantsConsumer(AbstractContextManager):
    """A terminator for variant processing pipelines."""

    @abc.abstractmethod
    def consume_one(self, full_variant: FullVariant) -> None:
        """Consume a single variant."""

    def consume(self, variants: Iterable[FullVariant]) -> None:
        """Consume variants."""
        for full_variant in variants:
            self.consume_one(full_variant)


class VariantsFilter(AbstractContextManager):
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


class VariantsBatchSource(AbstractContextManager):
    """A source that can fetch variants in batches."""

    @abc.abstractmethod
    def fetch_batches(
        self, region: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch variants in batches."""


class VariantsBatchConsumer(AbstractContextManager):
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


class VariantsBatchFilter(AbstractContextManager):
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
        return True


class VariantsLoaderSource(VariantsSource):
    """A source that can fetch variants from a loader."""

    def __init__(self, loader: VariantsGenotypesLoader) -> None:
        self.loader = loader

    def fetch(self, region: Region | None = None) -> Iterable[FullVariant]:
        """Fetch full variants from a variant loader."""
        yield from self.loader.fetch(region)

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        return exc_type is not None


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

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        return exc_type is not None


class VariantsPipelineProcessor(AbstractContextManager):
    """A processor that can be used to process variants in a pipeline."""

    def __init__(
        self,
        source: VariantsSource,
        filters: Sequence[VariantsFilter],
        consumer: VariantsConsumer,
    ) -> None:
        self.source = source
        self.filters = filters
        self.consumer = consumer

    def process_region(self, region: Region | None = None) -> None:
        for full_variant in self.source.fetch(region):
            for variant_filter in self.filters:
                full_variant = variant_filter.filter_one(full_variant)
            self.consumer.consume_one(full_variant)

    def process(self, regions: Iterable[Region] | None = None) -> None:
        """Process variants in batches for the given regions."""
        if regions is None:
            self.process_region(None)
            return
        for region in regions:
            self.process_region(region)

    def __enter__(self) -> VariantsPipelineProcessor:
        """Enter the context manager."""

        self.source.__enter__()
        for variant_filter in self.filters:
            variant_filter.__enter__()
        self.consumer.__enter__()

        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.source.__exit__(exc_type, exc_value, exc_tb)
        for variant_filter in self.filters:
            variant_filter.__exit__(exc_type, exc_value, exc_tb)
        self.consumer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None


class VariantsBatchPipelineProcessor:
    """A processor that can be used to process variants in a pipeline."""

    def __init__(
        self,
        source: VariantsBatchSource,
        filters: Sequence[VariantsBatchFilter],
        consumer: VariantsBatchConsumer,
    ) -> None:
        self.source = source
        self.filters = filters
        self.consumer = consumer

    def process_region(self, region: Region | None = None) -> None:
        for batch in self.source.fetch_batches(region):
            for variant_filter in self.filters:
                batch = variant_filter.filter_batch(batch)
            self.consumer.consume_batch(batch)

    def process(self, regions: Iterable[Region] | None = None) -> None:
        """Process variants in batches for the given regions."""
        if regions is None:
            self.process_region(None)
            return
        for region in regions:
            self.process_region(region)

    def __enter__(self) -> VariantsBatchPipelineProcessor:
        """Enter the context manager."""
        self.source.__enter__()
        for variant_filter in self.filters:
            variant_filter.__enter__()
        self.consumer.__enter__()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.source.__exit__(exc_type, exc_value, exc_tb)
        for variant_filter in self.filters:
            variant_filter.__exit__(exc_type, exc_value, exc_tb)
        self.consumer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None
