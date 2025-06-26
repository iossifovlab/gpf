# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613

import pathlib
from collections.abc import Sequence
from typing import Any

import pytest
from dae.annotation.annotation_pipeline import (
    Annotatable,
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
    AttributeInfo,
)
from dae.annotation.effect_annotator import EffectAnnotatorAdapter
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.parquet.schema2.processing_pipeline import (
    AnnotationPipelineVariantsBatchFilter,
    AnnotationPipelineVariantsFilter,
    VariantsBatchConsumer,
    VariantsBatchPipelineProcessor,
    VariantsConsumer,
    VariantsLoaderBatchSource,
    VariantsLoaderSource,
    VariantsPipelineProcessor,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.raw.loader import (
    FullVariant,
    VariantsGenotypesLoader,
)
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture
def study_1_loader(
    t4c8_study_1_data: tuple[pathlib.Path, pathlib.Path],
    t4c8_reference_genome: ReferenceGenome,
) -> VariantsGenotypesLoader:
    """Fixture to create a dummy loader for study 1."""
    ped_path, vcf_path = t4c8_study_1_data

    families = FamiliesLoader.load_pedigree_file(ped_path)

    return VcfLoader(
        families=families,
        vcf_files=[str(vcf_path)],
        genome=t4c8_reference_genome,
    )


def create_effect_annotator(
    pipeline: AnnotationPipeline,
    root_path: pathlib.Path,
) -> EffectAnnotatorAdapter:
    """Fixture to create a dummy effect annotator."""

    return EffectAnnotatorAdapter(
        pipeline=pipeline,
        info=AnnotatorInfo(
            "effect_annotator",
            annotator_id="A0",
            attributes=[
                AttributeInfo.create(
                    source="allele_effects",
                    name="allele_effects",
                    internal=True,
                ),
                AttributeInfo.create("worst_effect"),
                AttributeInfo.create("gene_effects"),
                AttributeInfo.create("effect_details"),
                AttributeInfo.create(
                    "gene_list",
                    name="gene_list",
                    internal=True,
                ),
            ],
            parameters={
                "genome": "t4c8_genome",
                "gene_models": "t4c8_genes",
                "work_dir": root_path / "effect_annotator" / "work",
            },
        ),
    )


@pytest.fixture
def effect_annotation_pipeline(
    t4c8_grr: GenomicResourceRepo,
    tmp_path: pathlib.Path,
) -> AnnotationPipeline:
    """Fixture to create a dummy annotation pipeline."""
    pipeline = AnnotationPipeline(
        t4c8_grr,
    )
    effect_annotator = create_effect_annotator(pipeline, tmp_path)
    pipeline.add_annotator(effect_annotator)
    return pipeline.open()


class DummyAnnotator(Annotator):
    """A dummy annotator that does nothing."""

    def __init__(self) -> None:
        attributes = [AttributeInfo(
            "index", "index",
            internal=False,
            parameters={})]
        info = AnnotatorInfo(
            "dummy_annotator",
            annotator_id="dummy",
            attributes=attributes,
            parameters={},
        )
        super().__init__(None, info)
        self.index = 0

    def open(self) -> Annotator:
        """Reset the annotator state."""
        self.index = 0
        return self

    def annotate(
        self, annotatable: Annotatable | None,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        """Produce annotation attributes for an annotatable."""
        if annotatable is None:
            return {}
        self.index += 1
        return {"index": self.index, "annotatable": annotatable}


@pytest.fixture
def dummy_annotation_pipeline(
    t4c8_grr: GenomicResourceRepo,
) -> AnnotationPipeline:
    """Fixture to create a dummy annotation pipeline."""
    pipeline = AnnotationPipeline(
        t4c8_grr,
    )
    dummy_annotator = DummyAnnotator()
    pipeline.add_annotator(dummy_annotator)

    return pipeline.open()


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
    result = list(batch_filter.filter_batch(variants))
    assert len(result) == 6


def test_dummy_annotation_pipeline_variants_batch_filter(
    dummy_annotation_pipeline: AnnotationPipeline,
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    batch_filter = AnnotationPipelineVariantsBatchFilter(
        dummy_annotation_pipeline)
    variants = list(study_1_loader.fetch())
    result = list(batch_filter.filter_batch(variants))
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
    result = list(annotation_filter.filter(variants))
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
    batches = list(batch_source.fetch_batches())
    assert len(batches) == expected_batches


class DummyBatchConsumer(VariantsBatchConsumer):

    def __init__(self) -> None:
        super().__init__()
        self.batches: list[list[FullVariant]] = []

    def consume_batch(self, batch: Sequence[FullVariant]) -> None:
        self.batches.append(list(batch))


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

    batch_processor = VariantsBatchPipelineProcessor(
        batch_source, [batch_filter], batch_consumer,
    )
    batch_processor.process()

    assert len(batch_consumer.batches) == expected_batches


class DummyConsumer(VariantsConsumer):
    """A dummy variants batch consumer."""

    def __init__(self) -> None:
        super().__init__()
        self.variants: list[FullVariant] = []

    def consume_one(self, full_variant: FullVariant) -> None:
        self.variants.append(full_variant)


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
        source, [annotation_filter], consumer,
    )
    processor.process()

    assert len(consumer.variants) == 6


def test_variants_consumer_consume(
    study_1_loader: VariantsGenotypesLoader,
) -> None:
    source = VariantsLoaderSource(
        study_1_loader,
    )
    consumer = DummyConsumer()
    consumer.consume(source.fetch())

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
    consumer.consume_batches(source.fetch_batches())

    assert len(consumer.batches) == expected_batches
