from box import Box

from dae.annotation.tools.file_io_parquet import ParquetReader
from dae.backends.import_commons import construct_import_annotation_pipeline
from dae.backends.impala.parquet_io import ParquetManager

from dae.tools.vcf2parquet import parse_cli_arguments, \
    generate_makefile, vcf2parquet


def test_vcf2parquet_vcf(
        vcf_import_config, annotation_pipeline_config,
        annotation_scores_dirname, temp_dirname,
        global_gpf_instance, dae_config_fixture, genomes_db):

    argv = [
        'vcf',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    argv = parse_cli_arguments(global_gpf_instance, argv)
    assert argv.type == 'vcf'

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config_fixture, genomes_db, argv, defaults={'values': {
            "scores_dirname": annotation_scores_dirname,
        }})
    parquet_manager = ParquetManager(dae_config_fixture.studies_db.dir)

    parquet_config = vcf2parquet(
        argv.pedigree, argv.vcf,
        genomes_db, annotation_pipeline, parquet_manager,
        argv.output, argv.bucket_index, argv.region
    )

    summary = ParquetReader(Box({
        'infile': parquet_config.files.variant,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    # print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    assert schema['effect_gene'].type_name == 'str'
    assert schema['effect_type'].type_name == 'str'
    assert schema['effect_data'].type_name == 'str'
    assert schema['worst_effect'].type_name == 'str'


def test_vcf2parquet_make(
        vcf_import_config, annotation_pipeline_config,
        annotation_scores_dirname, temp_dirname,
        global_gpf_instance, dae_config_fixture, default_genome):

    argv = [
        'make',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    argv = parse_cli_arguments(global_gpf_instance, argv)
    assert argv.type == 'make'

    generate_makefile(dae_config_fixture, default_genome, argv)
