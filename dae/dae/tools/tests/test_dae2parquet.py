import os

import pyarrow.parquet as pq

from dae.tools.dae2parquet import main


def test_dae2parquet_transmitted(
        dae_transmitted_config, annotation_pipeline_default_config,
        temp_filename,
        genomes_db_2013):

    argv = [
        'variants',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        # dae_transmitted_config.toomany_filename,
        # '--annotation', annotation_pipeline_default_config,
        '--ped-file-format', 'simple',
        '-o', temp_filename
    ]

    main(argv)

    os.path.exists(temp_filename)

    pqfile = pq.ParquetFile(temp_filename)
    schema = pqfile.schema
    assert 'effect_gene' in schema.names
    assert 'effect_type' in schema.names
    assert 'effect_data' in schema.names


def test_dae2parquet_make(
        dae_transmitted_config, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        genomes_db_2013):

    argv = [
        'make',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        # '--annotation', annotation_pipeline_default_config,
        '--ped-file-format', 'simple',
        '-o', temp_dirname,
    ]

    main(argv)

    assert os.path.exists(os.path.join(temp_dirname, 'Makefile'))
    with open(os.path.join(temp_dirname, 'Makefile'), 'rt') as infile:
        makefile = infile.read()

    print(makefile)

    assert 'all:' in makefile
    assert 'dae2parquet.py variants ' in makefile


def test_dae2parquet_make_partition(
        fixture_dirname, dae_transmitted_config,
        annotation_scores_dirname, temp_dirname,
        genomes_db_2013):

    partition_description = fixture_dirname(
        'backends/example_partition_configuration.conf')

    argv = [
        'make',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        '--ped-file-format', 'simple',
        '-o', temp_dirname,
        '--pd', partition_description
    ]

    main(argv)

    assert os.path.exists(os.path.join(temp_dirname, 'Makefile'))
    with open(os.path.join(temp_dirname, 'Makefile'), 'rt') as infile:
        makefile = infile.read()

    print(makefile)

    assert 'all:' in makefile
    assert 'dae2parquet.py variants ' in makefile
    assert '1_8' in makefile
    # assert '--region 1:800001-900000'
    assert '1_0' in makefile
    # assert '--region 1:1-100000'


def test_dae2parquet_dae_partition(
        fixture_dirname, dae_transmitted_config,
        temp_dirname):

    partition_description = fixture_dirname(
        'backends/example_partition_configuration.conf')

    argv = [
        'variants',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        '--ped-file-format', 'simple',
        '-o', temp_dirname,
        '--pd', partition_description
    ]

    main(argv)

    generated_conf = os.path.join(temp_dirname, '_PARTITION_DESCRIPTION')
    assert os.path.exists(generated_conf)
