import pyarrow as pa

from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_build_pipeline(
        annotation_config, anno_grdb):

    pipeline = AnnotationPipeline.build(
        annotation_config, anno_grdb
    )
    assert len(pipeline.annotators) == 3


def test_build_pipeline_schema(
        annotation_config, anno_grdb):

    pipeline = AnnotationPipeline.build(
        annotation_config, anno_grdb
    )

    schema = pipeline.annotation_schema
    assert schema is not None

    assert len(schema) == 10

    assert "effect_gene_genes" in schema.names
    field = schema.field("effect_gene_genes")
    assert field.type == pa.list_(pa.string())

    assert "cadd_raw" in schema.names
    field = schema.field("cadd_raw")
    assert field.type == pa.float32()
