from box import Box

from dae.annotation.annotation_pipeline import PipelineAnnotator
from dae.annotation.tools.file_io_parquet import ParquetSchema

from .conftest import relative_to_this_test_folder


def test_pipeline_schema(genomes_db_2013):
    filename = relative_to_this_test_folder('fixtures/import_annotation.conf')

    options = Box({
            'default_arguments': None,
            'vcf': True,
            'mode': 'overwrite',
        },
        default_box=True,
        default_box_attr=None)

    work_dir = relative_to_this_test_folder('fixtures/')

    pipeline = PipelineAnnotator.build(
        options, filename, work_dir, genomes_db_2013,
        defaults={'values': {'fixtures_dir': work_dir}}
    )
    assert pipeline is not None
    # print('pipeline annotators:', len(pipeline.annotators))

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

    # print(schema['effect_gene_genes'])
    assert schema['effect_gene_genes'].type_name == 'list(str)'
    assert schema['effect_gene_types'].type_name == 'list(str)'
    assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
    assert schema['effect_details_details'].type_name == 'list(str)'

    assert schema['effect_genes'].type_name == 'list(str)'
    assert schema['effect_details'].type_name == 'list(str)'
