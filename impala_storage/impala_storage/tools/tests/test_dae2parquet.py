# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import glob

import pyarrow.parquet as pq

from impala_storage.tools.dae2parquet import main


def test_dae2parquet_transmitted(
    dae_transmitted_config, temp_filename, gpf_instance_2019
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

    main(argv, gpf_instance=gpf_instance_2019)

    assert os.path.exists(temp_filename)

    files_glob = os.path.join(temp_filename, "*variants*.parquet")

    parquet_files = glob.glob(files_glob)
    assert len(parquet_files) == 1

    pqfile = pq.ParquetFile(parquet_files[0])
    schema = pqfile.schema
    assert "effect_gene_symbols" in schema.names
    assert "effect_types" in schema.names
    # assert "effect_data" in schema.names


def test_dae2parquet_dae_partition(
        fixture_dirname, dae_transmitted_config, temp_dirname,
        gpf_instance_2019):

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

    main(argv, gpf_instance=gpf_instance_2019)

    generated_conf = os.path.join(temp_dirname, "_PARTITION_DESCRIPTION")
    assert os.path.exists(generated_conf)
