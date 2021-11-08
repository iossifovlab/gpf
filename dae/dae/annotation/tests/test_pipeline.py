from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_build_pipeline(
        annotation_config, anno_grdb):

    config = AnnotationPipeline.load_and_parse(annotation_config)
    pipeline = AnnotationPipeline.build(
        config, anno_grdb
    )
    assert len(pipeline.annotators) == 5


def test_build_pipeline_schema(
        annotation_config, anno_grdb):

    config = AnnotationPipeline.load_and_parse(annotation_config)

    pipeline = AnnotationPipeline.build(
        config, anno_grdb
    )

    schema = pipeline.annotation_schema
    assert schema is not None

    # assert len(schema) == 10

    assert "effect_genes" in schema.names
    field = schema["effect_genes"]
    print(field, dir(field))

    assert field.type == "str", field

    assert "cadd_raw" in schema.names
    field = schema["cadd_raw"]
    assert field.type == "float"
