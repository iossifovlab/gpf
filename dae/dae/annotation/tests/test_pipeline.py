# pylint: disable=W0621,C0114,C0116,W0212,W0613
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

    attribute = pipeline.get_attribute_info("gene_effects")
    assert attribute is not None
    assert attribute.type == "str", attribute

    attribute = pipeline.get_attribute_info("cadd_raw")
    assert attribute is not None
    assert attribute.type == "float", attribute
