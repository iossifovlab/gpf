
from box import Box

from annotation.annotation_pipeline import PipelineAnnotator
from annotation.tools.file_io_parquet import ParquetSchema

from .conftest import relative_to_this_test_folder


def test_pipeline_schema():
    filename = relative_to_this_test_folder(
        "fixtures/import_annotation.conf")

    options = Box({
            "default_arguments": None,
            "vcf": True,
            "mode": "overwrite",
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename,
        defaults={
            "fixtures_dir": relative_to_this_test_folder("fixtures/")
        })
    assert pipeline is not None
    # print("pipeline annotators:", len(pipeline.annotators))

    schema = ParquetSchema()
    pipeline.collect_annotator_schema(schema)
    print(schema)

    assert 'phastCons100way' in schema
    assert 'RawScore' in schema
    assert 'PHRED' in schema

    # print(schema['PHRED'])
    assert schema['phastCons100way'].type_name == 'float'
    assert schema['RawScore'].type_name == 'float'
    assert schema['PHRED'].type_name == 'float'
