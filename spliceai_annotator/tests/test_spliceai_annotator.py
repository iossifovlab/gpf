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


def test_spliceai_annotate_del_acceptor(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatable = VCFAllele("10", 94076, "CAC", "C")
    result = spliceai_annotation_pipeline.annotate(annotatable)
    assert result is not None
    assert result["delta_score"] == \
        "C|TUBB8|0.19|0.15|0.00|0.05|90|-22|289|175"


def test_spliceai_annotate_ins_acceptor(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatable = VCFAllele("10", 94076, "C", "CCCCC")
    result = spliceai_annotation_pipeline.annotate(annotatable)
    assert result is not None
    assert result["delta_score"] == \
        "CCCCC|TUBB8|0.15|0.27|0.00|0.05|90|-22|-266|194"


def test_spliceai_annotate_simple_donor(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatable = VCFAllele("10", 94555, "C", "T")
    result = spliceai_annotation_pipeline.annotate(annotatable)
    assert result is not None
    assert result["delta_score"] == \
        "T|TUBB8|0.01|0.18|0.15|0.62|-2|110|-190|0"


def test_spliceai_batch_annotate(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatables = [
        VCFAllele("10", 94077, "A", "C"),
        VCFAllele("10", 94555, "C", "T"),
    ]
    result = spliceai_annotation_pipeline.batch_annotate(annotatables)
    assert result is not None
    assert len(result) == 2

    assert result[0]["delta_score"] == \
        "C|TUBB8|0.15|0.27|0.00|0.05|89|-23|-267|193"
    assert result[1]["delta_score"] == \
        "T|TUBB8|0.01|0.18|0.15|0.62|-2|110|-190|0"
