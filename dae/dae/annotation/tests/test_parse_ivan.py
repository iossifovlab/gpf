import pytest

from dae.annotation.annotation_pipeline import AnnotationPipeline


# @pytest.mark.skip(reason="not yet")
def test_empty():
    pipeline = AnnotationPipeline.build({})
    assert pipeline


@pytest.mark.skip(reason="not yet")
def test_effect_annotator():
    pipeline = AnnotationPipeline.AnnotationPipeline.parse_config('''
        - effect_annotator:
          gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
          genome: hg38/GRCh38-hg38/genome
    ''')
    assert pipeline
