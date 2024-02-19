# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import glob
from typing import Callable

import pyarrow.parquet as pq

from dae.gpf_instance.gpf_instance import GPFInstance

from impala_storage.tools.vcf2parquet import main


def test_vcf2parquet_vcf(
    fixture_dirname: Callable,
    annotation_pipeline_no_effects_config: str,
    annotation_scores_dirname: str,
    temp_filename: str,
    gpf_instance_2013: GPFInstance,
) -> None:

    prefix = fixture_dirname("vcf_import/effects_trio")
    argv = [
        "--rows", "10",
        "--annotation",
        annotation_pipeline_no_effects_config,
        "-o",
        temp_filename,
        f"{prefix}.ped",
        f"{prefix}.vcf.gz",
    ]

    main(
        argv,
        gpf_instance=gpf_instance_2013
    )

    files_glob = os.path.join(temp_filename, "*variants*.parquet")
    parquet_files = glob.glob(files_glob)
    assert len(parquet_files) == 1

    pqfile = pq.ParquetFile(parquet_files[0])
    schema = pqfile.schema

    assert "score0" in schema.names
    assert "score2" in schema.names
    assert "score4" in schema.names

    assert "effect_gene_symbols" in schema.names
    assert "effect_types" in schema.names
    assert "variant_data" in schema.names


def test_vcf2parquet_vcf_partition(
    fixture_dirname: Callable,
    annotation_pipeline_no_effects_config: str,
    annotation_scores_dirname: str,
    temp_dirname: str,
    gpf_instance_2013: GPFInstance,
) -> None:

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    prefix = fixture_dirname("vcf_import/effects_trio")
    argv = [
        "--rows", "10",
        "--annotation",
        annotation_pipeline_no_effects_config,
        "-o",
        temp_dirname,
        "--pd",
        partition_description,
        f"{prefix}.ped",
        f"{prefix}.vcf.gz",
    ]

    main(
        argv,
        gpf_instance=gpf_instance_2013
    )

    generated_conf = os.path.join(temp_dirname, "_PARTITION_DESCRIPTION")
    assert os.path.exists(generated_conf)
