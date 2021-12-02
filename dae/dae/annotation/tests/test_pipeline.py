from dae.annotation.annotation_factory import build_annotation_pipeline


def test_build_pipeline(
        annotation_config, grr_fixture):

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config,
        grr_repository=grr_fixture)

    assert len(pipeline.annotators) == 5


def test_build_pipeline_schema(
        annotation_config, grr_fixture):

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config,
        grr_repository=grr_fixture)

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
