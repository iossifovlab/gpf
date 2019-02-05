from box import Box

from configurable_entities.configuration import DAEConfig
from tools.dae2parquet import parse_cli_arguments, dae_build_denovo
from backends.configure import Configure
from annotation.tools.file_io_parquet import ParquetReader


def test_dae2parquet_denovo(
        dae_denovo_config, annotation_pipeline_configname, 
        annotation_scores_dirname,
        temp_dirname):

    argv = [
        'denovo',
        '--annotation', annotation_pipeline_configname,
        '-o', temp_dirname,
        '-f', 'simple',
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
    ]
    dae_config = DAEConfig()

    argv = parse_cli_arguments(dae_config, argv)

    assert argv is not None
    assert argv.type == 'denovo'

    dae_build_denovo(
        dae_config, argv, defaults={
            'scores_dirname': annotation_scores_dirname,
        })

    parquet_summary = Configure.from_prefix_parquet(
        temp_dirname).parquet.summary_variant
    summary = ParquetReader(Box({
        'infile': parquet_summary,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    # print(schema['effect_gene_genes'])
    assert schema['effect_gene_genes'].type_name == 'list(str)'
    assert schema['effect_gene_types'].type_name == 'list(str)'
    assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
    assert schema['effect_details_details'].type_name == 'list(str)'

    assert schema['effect_genes'].type_name == 'list(str)'
    assert schema['effect_details'].type_name == 'list(str)'

