import pytest
from box import Box

from dae.configuration.configuration import DAEConfig
from dae.annotation.tools.file_io_parquet import ParquetReader
from dae.backends.import_commons import construct_import_annotation_pipeline

from dae.backends.configure import Configure

from dae.tools.vcf2parquet import parse_cli_arguments, import_vcf, \
    generate_makefile


@pytest.mark.xfail(reason="annotation on import not ready for Impala")
def test_vcf2parquet_vcf(
        vcf_import_config, annotation_pipeline_config,
        annotation_scores_dirname,
        temp_dirname):

    argv = [
        'vcf',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    dae_config = DAEConfig.make_config()
    argv = parse_cli_arguments(dae_config, argv)
    assert argv.type == 'vcf'

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv, defaults={
            "scores_dirname": annotation_scores_dirname,
        })

    import_vcf(
        dae_config, annotation_pipeline,
        argv.pedigree, argv.vcf,
        region=argv.region, bucket_index=argv.bucket_index,
        output=argv.output)

    parquet_summary = Configure.from_prefix_parquet(
        temp_dirname, bucket_index=argv.bucket_index).parquet.summary_variant
    summary = ParquetReader(Box({
        'infile': parquet_summary,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    # print(schema['score0'])

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


@pytest.mark.xfail(reason="annotation on import not ready for Impala")
def test_vcf2parquet_make(
        vcf_import_config, annotation_pipeline_config,
        annotation_scores_dirname,
        temp_dirname):

    argv = [
        'make',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    dae_config = DAEConfig.make_config()
    argv = parse_cli_arguments(dae_config, argv)
    assert argv.type == 'make'

    generate_makefile(dae_config, argv)
