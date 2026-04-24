from __future__ import annotations

import itertools
import logging
import traceback
from collections.abc import Iterable, Sequence
from types import TracebackType
from typing import cast

from gain.annotation.annotate_utils import stringify
from gain.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from gain.annotation.processing_pipeline import (
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
)
from gain.effect_annotation.effect import AlleleEffects
from gain.utils.processing_pipeline import Filter, Source
from gain.utils.regions import Region

from gpf.parquet.schema2.loader import ParquetLoader
from gpf.variants.variant import SummaryAllele, SummaryVariant
from gpf.variants_loaders.raw.loader import (
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
        public_attributes = {}
        for key, value in annotation.context.items():
            if key in self._annotation_internal_attributes:
                continue
            ainfo = self.annotation_pipeline.get_attribute_info(key)
            if ainfo and ainfo.value_type == "str" and value is not None and \
                    not isinstance(value, str):
                value = stringify(value)
            public_attributes[key] = value
        summary_allele.update_attributes(public_attributes)


class DeleteAttributesFromVariantFilter(Filter):
    """Filter to remove items from variants. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self.to_remove = set(attributes_to_remove)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is None

    def filter(
        self, data: FullVariant,
    ) -> FullVariant:
        """Remove specified attributes from a variant."""
        for allele in data.summary_variant.alt_alleles:
            for attr in self.to_remove:
                if attr in allele.attributes:
                    del allele.attributes[attr]
        return data


class DeleteAttributesFromVariantsBatchFilter(Filter):
    """Filter to remove items from variant batches. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self._delete_filter = DeleteAttributesFromVariantFilter(
            attributes_to_remove)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is None

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
                exc_type, exc_value, traceback.format_tb(exc_tb))
        return exc_type is None

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
                exc_type, exc_value, traceback.format_tb(exc_tb))
        return exc_type is None

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

    def fetch(self, region: Region | None = None) -> Iterable[FullVariant]:
        """Fetch full variants from a variant loader."""
        yield from self.loader.fetch(region)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.loader.close()
        return exc_type is None


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
        self, region: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch full variants from a variant loader in batches."""
        variants = self.loader.fetch(region)
        while batch := tuple(itertools.islice(variants, self.batch_size)):
            yield batch

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.loader.close()
        return exc_type is None


class Schema2SummaryVariantsSource(Source):
    """Producer for summary variants from a Parquet dataset."""
    def __init__(self, loader: ParquetLoader):
        self.loader = loader

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[FullVariant]:
        assert self.loader is not None
        for sv in self.loader.fetch_summary_variants(region=region):
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
        self, region: Region | None = None,
    ) -> Iterable[Sequence[FullVariant]]:
        """Fetch full variants from a variant loader in batches."""
        variants = self.loader.fetch_summary_variants(region=region)
        while batch := tuple(itertools.islice(variants, self.batch_size)):
            yield [FullVariant(sv, ()) for sv in batch]
