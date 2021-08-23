from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_build_pipeline(
        annotation_config, anno_grdb):

    pipeline = AnnotationPipeline.build(
        annotation_config, anno_grdb
    )
    assert len(pipeline.annotators) == 2
