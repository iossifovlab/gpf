# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from box import Box
from dae.backends.schema2.parquet_io import (
    NoPartitionDescriptor, ParquetManager, ParquetPartitionDescriptor)
from dae.backends.vcf.loader import VcfLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.backends.storage.schema2_genotype_storage import \
    Schema2GenotypeStorage


@pytest.mark.parametrize("partition_description", [
    NoPartitionDescriptor(),
    ParquetPartitionDescriptor(["1"], region_length=5, family_bin_size=2),
])
def test_import_and_query(resources_dir, tmpdir, gpf_instance_2013,
                          partition_description):
    study_id = "testStudy"
    variants_dir = str(tmpdir)
    partition_description.output = variants_dir

    # run ped2parquet
    pedigree_parquet = str(tmpdir / "pedigree.parquet")
    _run_ped2parquet(str(resources_dir / "simple_variants.ped"),
                     pedigree_parquet)

    # run vcf2schema2 on the input vcf files
    _run_vcf2schema2(str(resources_dir / "simple_variants.ped"),
                     str(resources_dir / "simple_variants.vcf"),
                     gpf_instance_2013, partition_description)

    # create the storage
    config = {
        "impala": {
            "db": "impala_test_db",
            "hosts": ["localhost"],
            "port": 21050,
            "pool_size": 3,
        },
        "hdfs": {
            "base_dir": "/tests/test_schema2/studies",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
    }
    config = Box(config)
    storage = Schema2GenotypeStorage(config, "genotype_schema2")

    # clean hdfs from prev test runs and copy resulting parquets in hdfs
    study_dir = "/tests/test_schema2/studies/testStudy"
    if storage.hdfs_helpers.exists(study_dir):
        storage.hdfs_helpers.delete(study_dir, True)
    hdfs_study_layout = storage.hdfs_upload_dataset(
        study_id, variants_dir, pedigree_parquet, str(tmpdir / "meta.parquet"),
        partition_description)
    assert storage.hdfs_helpers.exists(study_dir)

    # load parquets in impala
    study_config = storage.import_dataset(
        study_id,
        hdfs_study_layout,
        partition_description=partition_description,
    )

    # query impala
    backend = storage.build_backend(Box(study_config), None,
                                    gpf_instance_2013.gene_models)
    family_variants = list(backend.query_variants())
    summary_variants = list(backend.query_summary_variants())

    # assert the number of summary and family allelies is as expected
    assert len(family_variants) == 5
    assert len(summary_variants) == 10
    # 10 reference and 18 alternative alleles
    assert sum(len(sv.alleles) for sv in summary_variants) == 28


def _run_vcf2schema2(ped_file, vcf_file, gpf_instance,
                     partition_description):
    pedigree = FamiliesLoader(ped_file).load()

    variants_loader = VcfLoader(
        pedigree,
        [vcf_file],
        params={
            "vcf_denovo_mode": "possible_denovo",
            "vcf_omission_mode": "possible_omission",
        },
        genome=gpf_instance.reference_genome,
    )

    ParquetManager.variants_to_parquet(
        variants_loader,
        partition_description,
        bucket_index=0,
        rows=20_000,
    )


def _run_ped2parquet(ped_file, output_filename):
    pedigree = FamiliesLoader(ped_file).load()
    ParquetManager.families_to_parquet(pedigree, output_filename)
