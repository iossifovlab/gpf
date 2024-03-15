# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import argparse

from typing import Callable

import pytest

from impala_storage.schema1.import_commons import BatchImporter, \
    SnakefileGenerator
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture
def cli_parse(gpf_instance_2013: GPFInstance) -> Callable:
    def parser(argv: list[str]) -> argparse.Namespace:
        parser = BatchImporter.cli_arguments_parser(gpf_instance_2013)
        return parser.parse_args(argv)

    return parser


@pytest.fixture
def importer(
    gpf_instance_2013: GPFInstance,
    hdfs_host: str, impala_host: str
) -> BatchImporter:

    storage_config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "impala": {
            "hosts": [impala_host],
            "port": 21050,
            "db": "genotype_impala",
            "pool_size": 5,
        },
        "hdfs": {
            "host": hdfs_host,
            "port": 8020,
            "base_dir": "/tmp/test_genotype_impala"},
    }
    gpf_instance_2013.genotype_storages.register_storage_config(
        storage_config
    )

    result = BatchImporter(gpf_instance_2013)
    assert result is not None
    return result


def test_makefile_generator_simple(
    fixture_dirname: Callable, cli_parse: Callable,
    importer: BatchImporter, temp_dirname: str
) -> None:
    prefix = fixture_dirname("vcf_import/effects_trio")
    argv = cli_parse(
        [
            "-o",
            temp_dirname,
            f"{prefix}.ped",
            "--vcf-files",
            f"{prefix}.vcf.gz",
            "--gs",
            "genotype_impala",
        ]
    )

    importer.build(argv)

    assert importer.study_id == "effects_trio"
    assert importer.vcf_loader is not None
    assert importer.denovo_loader is None
    assert importer.dae_loader is None


def test_makefile_generator_multivcf_simple(
    fixture_dirname: Callable, cli_parse: Callable,
    importer: BatchImporter, temp_dirname: str
) -> None:

    vcf_file1 = fixture_dirname("multi_vcf/multivcf_missing1.vcf.gz")
    vcf_file2 = fixture_dirname("multi_vcf/multivcf_missing2.vcf.gz")
    ped_file = fixture_dirname("multi_vcf/multivcf.ped")

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    argv = cli_parse(
        [
            "-o",
            temp_dirname,
            ped_file,
            "--vcf-files",
            vcf_file1,
            vcf_file2,
            "--pd",
            partition_description,
            "--gs",
            "genotype_impala",
        ]
    )

    importer.build(argv)

    assert importer.study_id == "multivcf"
    assert importer.partition_helper is not None
    assert importer.vcf_loader is not None
    assert importer.denovo_loader is None
    assert importer.dae_loader is None


def test_snakefile_generator_denovo_and_dae(
    fixture_dirname: Callable, cli_parse: Callable,
    importer: BatchImporter, temp_dirname: str
) -> None:

    denovo_file = fixture_dirname("dae_denovo/denovo.txt")
    dae_file = fixture_dirname("dae_transmitted/transmission.txt.gz")
    ped_file = fixture_dirname("dae_denovo/denovo_families.ped")

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    argv = cli_parse(
        [
            "--tool", "snakemake",
            "-o",
            temp_dirname,
            ped_file,
            "--id",
            "dae_denovo_and_transmitted",
            "--denovo-file",
            denovo_file,
            "--dae-summary-file",
            dae_file,
            "--pd",
            partition_description,
            "--gs",
            "genotype_impala",
        ]
    )

    importer.build(argv)

    assert importer.study_id == "dae_denovo_and_transmitted"
    assert importer.partition_helper is not None
    assert importer.vcf_loader is None
    assert importer.denovo_loader is not None
    assert importer.dae_loader is not None

    importer.generate_instructions(argv)

    assert os.path.exists(os.path.join(temp_dirname, "Snakefile"))
    with open(os.path.join(temp_dirname, "Snakefile"), "rt") as infile:
        makefile = infile.read()

    print(makefile)


CONTEXT = {
    "dae_db_dir":
    "/data/lubo/seq-pipeline/import_202005/production_mirror/data-hg19-test",
    "study_id": "test",
    "partition_description":
    "/data/lubo/seq-pipeline/import_202005/gpf_validation_data/"
    "data_hg19/studies/SPARKv3_pilot/partition_description.conf",
    "genotype_storage": "genotype_impala",
    "pedigree": {
        "pedigree":
        "/data/lubo/seq-pipeline/import_202005/gpf_validation_data/"
        "data_hg19/studies/SPARKv3_pilot/data/SPARKv3-families.ped",
        "output": "temp/pedigree.parquet",
        "params": "--ped-sex gender",
    },
    "variants_output": "temp/variants.parquet",
    "variants": {
        "denovo": {
            "bins": ["1_0", "2_0"],
            "variants":
            "/data/lubo/seq-pipeline/import_202005/gpf_validation_data/"
            "data_hg19/studies/SPARKv3_pilot/"
            "data/1394probands_denovoSNVindels_annotated5_pf_ia.csv",
            "params": "--denovo-chrom CHROM --denovo-pos POS --denovo-ref REF "
            "--denovo-alt ALT --denovo-person-id SPID ",
        }
    },
    "mirror_of": {
        "location":
        "cshlgroup@sparkgpf3-node03-prod.sfari.org:"
        "/data/import202005/data-hg19-test",
        "netloc": "/data/import202005/data-hg19-test",
    },
    "outdir": "./temp",
}


def test_snakefile_generator(temp_dirname: str) -> None:

    generator = SnakefileGenerator()
    result = generator.generate(CONTEXT)

    print(result)
    with open(os.path.join(temp_dirname, "Snakefile"), "wt") as outfile:
        outfile.write(result)


def test_generator_context_denovo_and_dae(
    fixture_dirname: Callable, cli_parse: Callable,
    importer: BatchImporter, temp_dirname: str
) -> None:

    denovo_file = fixture_dirname("dae_denovo/denovo.txt")
    dae_file = fixture_dirname("dae_transmitted/transmission.txt.gz")
    ped_file = fixture_dirname("dae_denovo/denovo_families.ped")

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    argv = cli_parse(
        [
            "--tool", "make",
            "-o",
            temp_dirname,
            ped_file,
            "--id",
            "dae_denovo_and_transmitted",
            "--denovo-file",
            denovo_file,
            "--dae-summary-file",
            dae_file,
            "--pd",
            partition_description,
            "--gs",
            "genotype_impala",
        ]
    )

    importer.build(argv)
    context = importer.build_context(argv)

    assert context is not None

    assert "dae_denovo_and_transmitted" == context["study_id"]

    assert "partition_description" in context
    assert partition_description == context["partition_description"]

    assert "dae" in context["variants"]
    assert "denovo" in context["variants"]

    assert dae_file == context["variants"]["dae"]["variants"]
    assert denovo_file == context["variants"]["denovo"]["variants"]

    assert "pedigree" in context
    assert ped_file == context["pedigree"]["pedigree"]


def test_generator_context_multivcf(
    fixture_dirname: Callable, cli_parse: Callable,
    importer: BatchImporter, temp_dirname: str
) -> None:

    vcf_file1 = fixture_dirname("multi_vcf/multivcf_missing1.vcf.gz")
    vcf_file2 = fixture_dirname("multi_vcf/multivcf_missing2.vcf.gz")
    ped_file = fixture_dirname("multi_vcf/multivcf.ped")

    partition_description = fixture_dirname(
        "backends/example_partition_configuration.conf"
    )

    argv = cli_parse(
        [
            "-o",
            temp_dirname,
            ped_file,
            "--vcf-files",
            vcf_file1,
            vcf_file2,
            "--pd",
            partition_description,
            "--gs",
            "genotype_impala",
        ]
    )

    importer.build(argv)
    context = importer.build_context(argv)

    assert context is not None

    assert "multivcf" == context["study_id"]

    assert "partition_description" in context
    assert partition_description == context["partition_description"]

    assert temp_dirname == context["outdir"]

    assert "vcf" in context["variants"]

    assert vcf_file1 in context["variants"]["vcf"]["variants"]
    assert vcf_file2 in context["variants"]["vcf"]["variants"]

    assert context["variants"]["vcf"]["params"] == ""

    assert ped_file == context["pedigree"]["pedigree"]
    assert context["pedigree"]["params"] == ""
