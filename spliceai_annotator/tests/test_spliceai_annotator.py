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


def test_spliceai_annotate_simple(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> None:
    annotatable = VCFAllele("10", 94077, "A", "C")
    result = spliceai_annotation_pipeline.annotate(annotatable)
    assert result is not None


def test_get_pos_data(
    spliceai_annotator: SpliceAIAnnotator,
) -> None:
    spliceai_annotator.open()
    gene_models = spliceai_annotator.gene_models
    transcript = gene_models.gene_models_by_location("10", 94077)[0]

    dist = spliceai_annotator._get_pos_data(transcript, 94077)
    assert dist[0] == -1184
    assert dist[1] == 1452
    assert dist[2] == -23
