import os

import pyarrow.parquet as pq

from dae.tools.vcf2parquet import main


def test_vcf2parquet_vcf(
    fixture_dirname,
    annotation_pipeline_config,
    annotation_scores_dirname,
    temp_filename,
    gpf_instance_2013,
):

    prefix = fixture_dirname("vcf_import/effects_trio")
    argv = [
        "--annotation",
        annotation_pipeline_config,
        "-o",
        temp_filename,
        f"{prefix}.ped",
        f"{prefix}.vcf.gz",
    ]

    main(
        argv,
        gpf_instance=gpf_instance_2013
    )

    assert os.path.exists(temp_filename)

    pqfile = pq.ParquetFile(temp_filename)
    schema = pqfile.schema

    assert "score0" in schema.names
    assert "score2" in schema.names
    assert "score4" in schema.names

    assert "effect_gene_symbols" in schema.names
    assert "effect_types" in schema.names
    assert "variant_data" in schema.names


def test_vcf2parquet_vcf_partition(
    fixture_dirname,
    annotation_pipeline_config,
    annotation_scores_dirname,
    temp_dirname,
    gpf_instance_2013,
):

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    prefix = fixture_dirname("vcf_import/effects_trio")
    argv = [
        "--annotation",
        annotation_pipeline_config,
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
