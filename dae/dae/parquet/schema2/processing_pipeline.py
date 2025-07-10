from __future__ import annotations

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
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
)
from dae.effect_annotation.effect import AlleleEffects
from dae.parquet.schema2.loader import ParquetLoader
from dae.utils.processing_pipeline import Filter, Source
from dae.utils.regions import Region
from dae.variants.variant import SummaryAllele, SummaryVariant
from dae.variants_loaders.raw.loader import (
    FullVariant,
    VariantsGenotypesLoader,
)

logger = logging.getLogger(__name__)


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

        if "allele_effects" in annotation.context:
            allele_effects = annotation.context["allele_effects"]
            assert isinstance(allele_effects, AlleleEffects)
            # pylint: disable=protected-access
            summary_allele._effects = allele_effects  # noqa: SLF001
            del annotation.context["allele_effects"]
        public_attributes = {
            key: value for key, value in annotation.context.items()
            if key not in self._annotation_internal_attributes
        }
        summary_allele.update_attributes(public_attributes)


class DeleteAttributesFromVariantFilter(Filter):
    """Filter to remove items from AWC contexts. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self.to_remove = set(attributes_to_remove)

    def filter(
        self, data: FullVariant,
    ) -> FullVariant:
        """Remove specified attributes from the context of an AWC."""
        for allele in data.summary_variant.alt_alleles:
            for attr in self.to_remove:
                if attr in allele.attributes:
                    del allele.attributes[attr]
        return data


class DeleteAttributesFromVariantsBatchFilter(Filter):
    """Filter to remove items from AWC contexts. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self._delete_filter = DeleteAttributesFromVariantFilter(
            attributes_to_remove)

    def filter(
        self, data: Sequence[FullVariant],
    ) -> Sequence[FullVariant]:
        """Remove specified attributes from batches of variants."""
        for variant in data:
            self._delete_filter.filter(variant)
        return data


class AnnotationPipelineVariantsFilter(
    Filter,
    AnnotationPipelineVariantsFilterMixin,
):
    """Annotation pipeline batched variants filter."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        super().__init__(annotation_pipeline)
        self.annotatables_filter = AnnotationPipelineAnnotatablesFilter(
            annotation_pipeline)

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

    def filter(self, data: FullVariant) -> FullVariant:
        variant = AnnotationsWithSource(
            source=data,
            annotations=[
                Annotation(sa.get_annotatable(), dict(sa.attributes))
                for sa in data.summary_variant.alt_alleles
            ],
        )
        aws = self.annotatables_filter.filter(variant)

        full_variant = cast(FullVariant, aws.source)
        assert isinstance(full_variant.summary_variant, SummaryVariant)
        assert len(aws.annotations) == \
            len(full_variant.summary_variant.alt_alleles)
        for summary_allele, annotation in zip(
                full_variant.summary_variant.alt_alleles,
                aws.annotations, strict=True):
            assert isinstance(summary_allele, SummaryAllele)
            self._apply_annotation_to_allele(summary_allele, annotation)
        return full_variant


class AnnotationPipelineVariantsBatchFilter(
    Filter,
    AnnotationPipelineVariantsFilterMixin,
):
    """Annotation pipeline batched variants filter."""

    def __init__(self, annotation_pipeline: AnnotationPipeline) -> None:
        super().__init__(annotation_pipeline)
        self.annotatables_filter = AnnotationPipelineAnnotatablesBatchFilter(
            annotation_pipeline)

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
        return True

    def filter(
        self, data: Sequence[FullVariant],
    ) -> Sequence[FullVariant]:
        """Filter variants in batches."""
        variants = [
            AnnotationsWithSource(
                source=v,
                annotations=[
                    Annotation(sa.get_annotatable(), dict(sa.attributes))
                    for sa in v.summary_variant.alt_alleles
                ],
            )
            for v in data
        ]
        aws_batch = \
            self.annotatables_filter.filter(variants)

        result: list[FullVariant] = []
        for aws in aws_batch:
            full_variant = cast(FullVariant, aws.source)
            assert isinstance(full_variant.summary_variant, SummaryVariant)
            assert len(aws.annotations) == \
                len(full_variant.summary_variant.alt_alleles)
            for summary_allele, annotation in zip(
                    full_variant.summary_variant.alt_alleles,
                    aws.annotations, strict=True):
                assert isinstance(summary_allele, SummaryAllele)
                self._apply_annotation_to_allele(summary_allele, annotation)

            result.append(full_variant)
        return result


class VariantsLoaderSource(Source):
    """A source that can fetch variants from a loader."""

    def __init__(self, loader: VariantsGenotypesLoader) -> None:
        self.loader = loader

    def fetch(self, data: Region | None = None) -> Iterable[FullVariant]:
        """Fetch full variants from a variant loader."""
        yield from self.loader.fetch(data)


class VariantsLoaderBatchSource(Source):
    """A source that can fetch variants in batches from a loader."""

    def __init__(
        self,
        loader: VariantsGenotypesLoader,
        batch_size: int = 500,
    ) -> None:
        self.loader = loader
        self.batch_size = batch_size

    def fetch(
        self, data: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch full variants from a variant loader in batches."""
        variants = self.loader.fetch(data)
        while batch := tuple(itertools.islice(variants, self.batch_size)):
            yield batch


class VariantsPipelineProcessor(AbstractContextManager):
    """A processor that can be used to process variants in a pipeline."""

    def __init__(self, source: Source, filters: Sequence[Filter]) -> None:
        self.source = source
        self.filters = filters

    def __enter__(self) -> VariantsPipelineProcessor:
        self.source.__enter__()
        for variant_filter in self.filters:
            variant_filter.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.source.__exit__(exc_type, exc_value, exc_tb)
        for variant_filter in self.filters:
            variant_filter.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def process_region(self, region: Region | None = None) -> None:
        for data in self.source.fetch(region):
            for _filter in self.filters:
                data = _filter.filter(data)

    def process(self, regions: Iterable[Region] | None = None) -> None:
        """Process variants in batches for the given regions."""
        if regions is None:
            self.process_region(None)
            return
        for region in regions:
            self.process_region(region)


class Schema2SummaryVariantsSource(Source):
    """Producer for summary variants from a Parquet dataset."""
    def __init__(self, loader: ParquetLoader):
        self.loader = loader

    def fetch(
        self, data: Region | None = None,
    ) -> Iterable[FullVariant]:
        assert self.loader is not None
        for sv in self.loader.fetch_summary_variants(region=data):
            yield FullVariant(sv, ())


class Schema2SummaryVariantsBatchSource(Source):
    """Producer for summary variants from a Parquet dataset."""

    def __init__(
        self,
        loader: ParquetLoader,
        batch_size: int = 500,
    ) -> None:
        self.loader = loader
        self.batch_size = batch_size

    def fetch(
        self, data: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch full variants from a variant loader in batches."""
        variants = self.loader.fetch_summary_variants(region=data)
        while batch := tuple(itertools.islice(variants, self.batch_size)):
            yield [FullVariant(sv, ()) for sv in batch]
