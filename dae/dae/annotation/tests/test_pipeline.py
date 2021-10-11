import pyarrow as pa

from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_build_pipeline(
        annotation_config, anno_grdb):

    pipeline = AnnotationPipeline.build(
        annotation_config, anno_grdb
    )
    assert len(pipeline.annotators) == 5


def test_build_pipeline_schema(
        annotation_config, anno_grdb):

    pipeline = AnnotationPipeline.build(
        annotation_config, anno_grdb
    )

    schema = pipeline.annotation_schema
    assert schema is not None

    # assert len(schema) == 10

    assert "effect_gene_genes" in schema.names
    field = schema["effect_gene_genes"]
    print(field, dir(field))

    assert field.type == pa.list_(pa.string()), field

    assert "cadd_raw" in schema.names
    field = schema["cadd_raw"]
    assert field.type == pa.float32()
