import pytest
from dae.annotation.annotation_pipeline import AnnotationPipeline


@pytest.mark.skip(reason="not yet")
def test_empty():
    pipeline = AnnotationPipeline.build({})
    assert pipeline
