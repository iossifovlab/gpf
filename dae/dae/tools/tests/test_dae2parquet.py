import os

import pyarrow.parquet as pq

from dae.tools.dae2parquet import main


def test_dae2parquet_transmitted(
    dae_transmitted_config, temp_filename, genomes_db_2013
):

    argv = [
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        "--ped-file-format",
        "simple",
        "-o",
        temp_filename,
        "--rows", "10",
    ]

    main(argv)

    os.path.exists(temp_filename)

    pqfile = pq.ParquetFile(temp_filename)
    schema = pqfile.schema
    assert "effect_gene_symbols" in schema.names
    assert "effect_types" in schema.names
    # assert "effect_data" in schema.names


def test_dae2parquet_dae_partition(
        fixture_dirname, dae_transmitted_config, temp_dirname):

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    argv = [
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        "--ped-file-format",
        "simple",
        "-o",
        temp_dirname,
        "--pd",
        partition_description,
        "--rows", "10",
    ]

    main(argv)

    generated_conf = os.path.join(temp_dirname, "_PARTITION_DESCRIPTION")
    assert os.path.exists(generated_conf)
