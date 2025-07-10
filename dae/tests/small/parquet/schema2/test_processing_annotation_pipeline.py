# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613

from collections.abc import Sequence

import pytest
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
)
from dae.parquet.schema2.processing_pipeline import (
    AnnotationPipelineVariantsBatchFilter,
    AnnotationPipelineVariantsFilter,
    VariantsLoaderBatchSource,
    VariantsLoaderSource,
    VariantsPipelineProcessor,
)
from dae.utils.processing_pipeline import Filter
from dae.variants_loaders.raw.loader import (
    FullVariant,
    VariantsGenotypesLoader,
)


def test_study_1_loader(
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    assert study_1_loader is not None
    variants = list(study_1_loader.fetch())
    assert len(variants) == 6


def test_effect_annotation_pipeline_variants_batch_filter(
    effect_annotation_pipeline: AnnotationPipeline,
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    batch_filter = AnnotationPipelineVariantsBatchFilter(
        effect_annotation_pipeline)
    variants = list(study_1_loader.fetch())
    with batch_filter as batch_filter:
        result = list(batch_filter.filter(variants))
    result = list(batch_filter.filter(variants))
    assert len(result) == 6


def test_dummy_annotation_pipeline_variants_batch_filter(
    dummy_annotation_pipeline: AnnotationPipeline,
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    batch_filter = AnnotationPipelineVariantsBatchFilter(
        dummy_annotation_pipeline)
    variants = list(study_1_loader.fetch())

    result = []
    with batch_filter as batch_filter:
        result = list(batch_filter.filter(variants))
    assert len(result) == 6
    index = 0
    for full_variant in result:
        assert isinstance(full_variant, FullVariant)
        sv = full_variant.summary_variant
        for sa in sv.alt_alleles:
            index += 1
            assert sa.attributes["index"] == index
    assert index == 11


def test_dummy_annotation_pipeline_variants_filter(
    dummy_annotation_pipeline: AnnotationPipeline,
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    annotation_filter = AnnotationPipelineVariantsFilter(
        dummy_annotation_pipeline)
    variants = list(study_1_loader.fetch())
    result = []
    with annotation_filter as annotation_filter:
        result = [annotation_filter.filter(variant) for variant in variants]
    assert len(result) == 6
    index = 0
    for full_variant in result:
        assert isinstance(full_variant, FullVariant)
        sv = full_variant.summary_variant
        for sa in sv.alt_alleles:
            index += 1
            assert sa.attributes["index"] == index
    assert index == 11


@pytest.mark.parametrize(
    "batch_size, expected_batches",
    [
        (1, 6),
        (2, 3),
        (3, 2),
        (4, 2),
        (5, 2),
        (6, 1),
        (7, 1),
        (500, 1),
    ],
)
def test_variants_loader_batch_source(
    study_1_loader: VariantsGenotypesLoader,
    batch_size: int,
    expected_batches: int,
) -> None:
    batch_source = VariantsLoaderBatchSource(
        study_1_loader, batch_size=batch_size)
    batches = list(batch_source.fetch())
    assert len(batches) == expected_batches


class DummyBatchConsumer(Filter):
    def __init__(self) -> None:
        super().__init__()
        self.batches: list[list[FullVariant]] = []

    def filter(self, data: Sequence[FullVariant]) -> None:
        self.batches.append(list(data))


@pytest.mark.parametrize(
    "batch_size, expected_batches",
    [
        (1, 6),
        (2, 3),
        (3, 2),
        (4, 2),
        (5, 2),
        (6, 1),
        (7, 1),
        (500, 1),
    ],
)
def test_variants_batch_pipeline_processor(
    study_1_loader: VariantsGenotypesLoader,
    dummy_annotation_pipeline: AnnotationPipeline,
    batch_size: int,
    expected_batches: int,
) -> None:
    batch_source = VariantsLoaderBatchSource(
        study_1_loader, batch_size=batch_size,
    )
    batch_consumer = DummyBatchConsumer()
    batch_filter = AnnotationPipelineVariantsBatchFilter(
        dummy_annotation_pipeline,
    )

    batch_processor = VariantsPipelineProcessor(
        batch_source, [batch_filter, batch_consumer])
    batch_processor.process()

    assert len(batch_consumer.batches) == expected_batches


class DummyConsumer(Filter):
    """A dummy variants batch consumer."""

    def __init__(self) -> None:
        super().__init__()
        self.variants: list[FullVariant] = []

    def filter(self, data: FullVariant) -> None:
        self.variants.append(data)


def test_variants_pipeline_processor(
    study_1_loader: VariantsGenotypesLoader,
    dummy_annotation_pipeline: AnnotationPipeline,
) -> None:
    source = VariantsLoaderSource(
        study_1_loader,
    )
    consumer = DummyConsumer()
    annotation_filter = AnnotationPipelineVariantsFilter(
        dummy_annotation_pipeline,
    )

    processor = VariantsPipelineProcessor(
        source, [annotation_filter, consumer])
    processor.process()

    assert len(consumer.variants) == 6


def test_variants_consumer_consume(
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    source = VariantsLoaderSource(
        study_1_loader,
    )
    consumer = DummyConsumer()
    for data in source.fetch():
        consumer.filter(data)

    assert len(consumer.variants) == 6


@pytest.mark.parametrize(
    "batch_size, expected_batches",
    [
        (1, 6),
        (2, 3),
        (3, 2),
        (4, 2),
        (5, 2),
        (6, 1),
        (7, 1),
        (500, 1),
    ],
)
def test_variants_batch_consumer_consume(
    study_1_loader: VariantsGenotypesLoader,
    batch_size: int,
    expected_batches: int,
) -> None:
    source = VariantsLoaderBatchSource(
        study_1_loader,
        batch_size=batch_size,
    )
    consumer = DummyBatchConsumer()
    for data in source.fetch():
        consumer.filter(data)

    assert len(consumer.batches) == expected_batches
