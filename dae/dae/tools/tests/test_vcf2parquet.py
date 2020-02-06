import os

import pyarrow.parquet as pq

from dae.tools.vcf2parquet import main


def test_vcf2parquet_vcf(
        fixture_dirname, annotation_pipeline_config,
        annotation_scores_dirname, temp_filename,
        gpf_instance_2013):

    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = [
        'variants',
        '--annotation', annotation_pipeline_config,
        '-o', temp_filename,
        f'{prefix}.ped',
        f'{prefix}.vcf.gz',
    ]

    main(
        argv, gpf_instance=gpf_instance_2013,
        annotation_defaults={'values': {
             "scores_dirname": annotation_scores_dirname,
        }}
    )

    assert os.path.exists(temp_filename)

    pqfile = pq.ParquetFile(temp_filename)
    schema = pqfile.schema

    assert 'score0' in schema.names
    assert 'score2' in schema.names
    assert 'score4' in schema.names

    assert 'effect_gene' in schema.names
    assert 'effect_type' in schema.names
    assert 'effect_data' in schema.names


def test_vcf2parquet_vcf_partition(
        fixture_dirname, annotation_pipeline_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013,
        parquet_partition_configuration):

    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = [
        'variants',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration,
        f'{prefix}.ped',
        f'{prefix}.vcf.gz'
    ]

    main(
        argv, gpf_instance=gpf_instance_2013,
        annotation_defaults={'values': {
             "scores_dirname": annotation_scores_dirname,
        }}
    )

    generated_conf = os.path.join(temp_dirname, '_PARTITION_DESCRIPTION')
    assert os.path.exists(generated_conf)


def test_vcf2parquet_make(
        fixture_dirname, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genome_2013):

    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = [
        'make',
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        f'{prefix}.ped',
        f'{prefix}.vcf.gz',
    ]

    main(argv)

    assert os.path.exists(os.path.join(temp_dirname, 'Makefile'))
    with open(os.path.join(temp_dirname, 'Makefile'), 'rt') as infile:
        makefile = infile.read()

    print(makefile)

    assert 'all:' in makefile
    assert 'vcf2parquet.py variants ' in makefile


def test_vcf2parquet_make_partition(
        fixture_dirname, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genome_2013,
        parquet_partition_configuration):

    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = [
        'make',
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration,
        f'{prefix}.ped',
        f'{prefix}.vcf.gz',
    ]

    main(argv)

    assert os.path.exists(os.path.join(temp_dirname, 'Makefile'))
    with open(os.path.join(temp_dirname, 'Makefile'), 'rt') as infile:
        makefile = infile.read()

    print(makefile)
    assert 'all:' in makefile
    assert 'vcf2parquet.py variants ' in makefile
    assert '2_8' in makefile
    # assert '--region 1:80000001-90000000' in makefile
    assert '2_9' in makefile
    # assert '--region 1:90000001-100000000' in makefile
    assert '2_12' in makefile
    # assert '--region 1:120000001-130000000' in makefile


def test_vcf2parquet_make_partition_target_chromosomes(
        fixture_dirname, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genome_2013,
        parquet_partition_configuration):

    prefix = fixture_dirname('vcf_import/effects_trio')
    argv = [
        'make',
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration,
        f'{prefix}.ped',
        f'{prefix}.vcf.gz',
        '--tc', '1',
    ]

    main(argv)

    assert os.path.exists(os.path.join(temp_dirname, 'Makefile'))
    with open(os.path.join(temp_dirname, 'Makefile'), 'rt') as infile:
        makefile = infile.read()

    print(makefile)
    assert 'all:' in makefile
    assert 'vcf2parquet.py variants ' in makefile
    assert '2_8' not in makefile
    assert '2_9' not in makefile
    assert '2_12' not in makefile
