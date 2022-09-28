# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import glob
import pyarrow.parquet as pq

from dae.tools.denovo2parquet import main
from dae.impala_storage.parquet_io import ParquetPartitionDescriptor


def test_denovo2parquet_denovo(
        dae_denovo_config, temp_filename, gpf_instance_2019):

    argv = [
        "--ped-file-format",
        "simple",
        "-o",
        temp_filename,
        dae_denovo_config.pedigree,
        dae_denovo_config.denovo,
    ]

    main(argv, gpf_instance=gpf_instance_2019)

    assert os.path.exists(temp_filename)

    files_glob = os.path.join(temp_filename, "*variants.parquet")
    parquet_files = glob.glob(files_glob)
    assert len(parquet_files) == 1

    pqfile = pq.ParquetFile(parquet_files[0])
    schema = pqfile.schema

    assert "effect_gene_symbols" in schema.names
    assert "effect_types" in schema.names
    assert "variant_data" in schema.names


def test_denovo2parquet_denovo_partition(
        fixture_dirname, dae_denovo_config, temp_dirname, gpf_instance_2019):

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    argv = [
        "--ped-file-format",
        "simple",
        "--pd",
        partition_description,
        "-o",
        temp_dirname,
        dae_denovo_config.pedigree,
        dae_denovo_config.denovo,
    ]

    main(argv, gpf_instance=gpf_instance_2019)

    part_desc = ParquetPartitionDescriptor.from_config(partition_description)
    file_glob = os.path.join(
        temp_dirname, part_desc.generate_file_access_glob())
    partition_files = glob.glob(file_glob)

    assert len(partition_files) == 5
    for file in partition_files:
        assert "frequency_bin=0" in file
