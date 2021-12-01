import pytest

from dae.annotation.annotation_factory import build_annotation_pipeline


# @pytest.mark.skip(reason="not yet")
def test_empty():
    pipeline = build_annotation_pipeline([])
    assert pipeline


@pytest.mark.skip(reason="not yet")
def test_effect_annotator():
    pipeline = build_annotation_pipeline(
        pipeline_config_str='''
        - effect_annotator:
          gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
          genome: hg38/GRCh38-hg38/genome
        ''')
    assert pipeline
