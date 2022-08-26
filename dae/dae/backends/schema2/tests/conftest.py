# pylint: disable=W0621,C0114,C0116,W0212,W0613

import tempfile
import pytest
from box import Box
from dae.backends.vcf.loader import VcfLoader
from dae.backends.dae.loader import DenovoLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.backends.storage.schema2_genotype_storage import \
    Schema2GenotypeStorage
from dae.backends.schema2.parquet_io import (
    NoPartitionDescriptor, ParquetManager, ParquetPartitionDescriptor)


@pytest.fixture(scope="module")
def storage():
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
    return Schema2GenotypeStorage(config, "genotype_schema2")


@pytest.fixture(scope="module")
def import_test_study(resources_dir, gpf_instance_2013, storage):
    def importer(
        study_id, tmpdir, partition_description, variant_files,
        loader_args=None
    ):
        partition_description.output = tmpdir

        # generate parquets
        pedigree_parquet = f"{tmpdir}/pedigree.parquet"
        run_ped2parquet(f"{resources_dir}/simple_variants.ped",
                        pedigree_parquet)
        for filename in variant_files:
            file_type = "vcf" if filename.endswith("vcf") else "denovo"
            to_parquet_func = {
                "vcf": run_vcf2schema2,
                "denovo": run_denovo2schema2
            }[file_type]
            to_parquet_func(
                f"{resources_dir}/simple_variants.ped",
                f"{resources_dir}/{filename}",
                gpf_instance_2013, partition_description,
                loader_args=loader_args
            )

        # clean hdfs from prev test runs and copy resulting parquets in hdfs
        study_dir = f"/tests/test_schema2/studies/{study_id}"
        if storage.hdfs_helpers.exists(study_dir):
            storage.hdfs_helpers.delete(study_dir, True)
        hdfs_study_layout = storage.hdfs_upload_dataset(
            study_id, tmpdir, pedigree_parquet, f"{tmpdir}/meta.parquet",
            partition_description)

        # load parquets in impala
        study_config = storage.import_dataset(
            study_id,
            hdfs_study_layout,
            partition_description=partition_description,
        )

        backend = storage.build_backend(Box(study_config), None,
                                        gpf_instance_2013.gene_models)
        return backend
    return importer


@pytest.fixture(
    scope="session",
    params=[
        NoPartitionDescriptor(),
        ParquetPartitionDescriptor(["1"], region_length=5, family_bin_size=2),
    ]
)
def partition_description(request):
    return request.param


@pytest.fixture(scope="module")
def testing_study_backend(
    partition_description, import_test_study
):
    """Import a test study and return the backend used to query it."""
    study_id = "testStudyVcf"
    with tempfile.TemporaryDirectory() as tmpdir:
        yield import_test_study(
            study_id, tmpdir, partition_description, ["simple_variants.vcf"]
        )


def run_vcf2schema2(ped_file, vcf_file, gpf_instance,
                    partition_description, loader_args=None):
    pedigree = FamiliesLoader(ped_file).load()

    loader_args = loader_args if loader_args else {}
    variants_loader = VcfLoader(
        pedigree,
        [vcf_file],
        params={
            "vcf_denovo_mode": "possible_denovo",
            "vcf_omission_mode": "possible_omission",
        },
        genome=gpf_instance.reference_genome,
        **loader_args,
    )

    ParquetManager.variants_to_parquet(
        variants_loader,
        partition_description,
        bucket_index=0,
        rows=20_000,
    )


def run_denovo2schema2(ped_file, denovo_file, gpf_instance,
                       partition_description, loader_args=None):
    pedigree = FamiliesLoader(ped_file).load()

    loader_args = loader_args if loader_args else {}
    variants_loader = DenovoLoader(
        pedigree,
        denovo_file,
        genome=gpf_instance.reference_genome,
        **loader_args,
    )

    ParquetManager.variants_to_parquet(
        variants_loader,
        partition_description,
        bucket_index=100,
        rows=20_000,
    )


def run_ped2parquet(ped_file, output_filename):
    pedigree = FamiliesLoader(ped_file).load()
    ParquetManager.families_to_parquet(pedigree, output_filename)
