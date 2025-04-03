# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_pipeline import AnnotationPipeline
from spliceai_annotator.spliceai_annotator import SpliceAIAnnotator


def test_spliceai_annotator(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    """Test SpliceAI annotator."""
    pipeline = spliceai_annotation_pipeline
    assert pipeline is not None
    assert pipeline.annotators is not None
    assert len(pipeline.annotators) == 1
    assert isinstance(pipeline.annotators[0], SpliceAIAnnotator)


def test_spliceai_annotate_simple_acceptor(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatable = VCFAllele("10", 94077, "A", "C")
    result = spliceai_annotation_pipeline.annotate(annotatable)
    assert result is not None
    assert result["delta_score"] == \
        "C|TUBB8|0.15|0.27|0.00|0.05|89|-23|-267|193"


def test_spliceai_annotate_simple_donor(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatable = VCFAllele("10", 94555, "C", "T")
    result = spliceai_annotation_pipeline.annotate(annotatable)
    assert result is not None
    assert result["delta_score"] == \
        "T|TUBB8|0.01|0.18|0.15|0.62|-2|110|-190|0"


def test_padding_size(
    spliceai_annotator: SpliceAIAnnotator,
) -> None:
    spliceai_annotator.open()

    gene_models = spliceai_annotator.gene_models
    transcript = gene_models.gene_models_by_location("10", 94077)[0]

    padding = spliceai_annotator._padding_size(transcript, 94077)
    assert padding[0] == 4316
    assert padding[1] == 4048
