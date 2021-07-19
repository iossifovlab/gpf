from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_build_pipeline(
    annotation_config, anno_grdb, genomes_db_2013,
):
    pipeline = AnnotationPipeline.build(
        annotation_config, genomes_db_2013, anno_grdb
    )
    assert len(pipeline.annotators) == 2
