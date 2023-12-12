# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from typing import Callable, Iterator, Union, Optional, cast, \
    Any

import pytest
from box import Box

from dae.gpf_instance import GPFInstance
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.parquet_writer import ParquetWriter
from dae.parquet.schema2.parquet_io import \
    VariantsParquetWriter as S2VariantsWriter
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator
from dae.import_tools.import_tools import \
    construct_import_annotation_pipeline

from impala_storage.schema2.impala2_genotype_storage import \
    Impala2GenotypeStorage
from impala_storage.schema2.impala_variants import ImpalaVariants


@pytest.fixture(scope="module")
def storage() -> Impala2GenotypeStorage:
    config = {
        "id": "genotype_schema2",
        "storage_type": "impala2",
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
    return Impala2GenotypeStorage(config)


@pytest.fixture(scope="module")
def import_test_study(
        resources_dir: str,
        gpf_instance_2013: GPFInstance,
        storage: Impala2GenotypeStorage) -> Callable:

    def importer(
        study_id: str,
        tmpdir: str,
        partition_description: PartitionDescriptor,
        variant_files: list[str],
        loader_args: Optional[dict] = None
    ) -> ImpalaVariants:

        # generate parquets
        pedigree_parquet = run_ped2parquet(
            f"{resources_dir}/simple_variants.ped", tmpdir)
        for filename in variant_files:
            file_type = "vcf" if filename.endswith("vcf") else "denovo"
            to_parquet_func = {
                "vcf": run_vcf2schema2,
                "denovo": run_denovo2schema2
            }[file_type]
            to_parquet_func(
                tmpdir,
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
            study_id, tmpdir, pedigree_parquet, f"{tmpdir}/meta/meta.parquet")

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
        PartitionDescriptor(),
        PartitionDescriptor(
            chromosomes=["1"], region_length=50, family_bin_size=2),
    ]
)
def partition_description(
        request: pytest.FixtureRequest) -> PartitionDescriptor:
    return cast(PartitionDescriptor, request.param)


@pytest.fixture(scope="module")
def testing_study_backend(
    partition_description: PartitionDescriptor,
    import_test_study: Callable,
    tmp_path_factory: pytest.TempPathFactory
) -> Iterator[ImpalaVariants]:
    """Import a test study and return the backend used to query it."""
    study_id = "testStudyVcf"
    tmpdir = tmp_path_factory.mktemp("testing_study_backend")
    yield import_test_study(
        study_id, str(tmpdir), partition_description, ["simple_variants.vcf"]
    )


def run_vcf2schema2(
    out_dir: str, ped_file: str, vcf_file: str,
    gpf_instance: GPFInstance,
    partition_description: PartitionDescriptor,
    loader_args: Optional[dict[str, Any]] = None
) -> None:
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
    loader = build_variants_loader_pipeline(
        variants_loader, gpf_instance
    )

    ParquetWriter.variants_to_parquet(
        out_dir,
        loader,
        partition_description,
        S2VariantsWriter,
        bucket_index=0,
        rows=20_000,
    )
    ParquetWriter.write_meta(
        out_dir,
        loader,
        partition_description,
        S2VariantsWriter,
    )


def run_denovo2schema2(
    out_dir: str, ped_file: str, denovo_file: str,
    gpf_instance: GPFInstance,
    partition_description: PartitionDescriptor,
    loader_args: Optional[dict[str, Any]] = None
) -> None:
    pedigree = FamiliesLoader(ped_file).load()

    loader_args = loader_args if loader_args else {}
    variants_loader = DenovoLoader(
        pedigree,
        denovo_file,
        genome=gpf_instance.reference_genome,
        **loader_args,
    )
    loader = build_variants_loader_pipeline(
        variants_loader, gpf_instance
    )

    ParquetWriter.variants_to_parquet(
        out_dir,
        loader,
        partition_description,
        S2VariantsWriter,
        bucket_index=100,
        rows=20_000,
    )
    ParquetWriter.write_meta(
        out_dir,
        loader,
        partition_description,
        S2VariantsWriter,
    )


def run_ped2parquet(ped_file: str, output_dir: str) -> str:
    pedigree = FamiliesLoader(ped_file).load()
    output_filename = os.path.join(output_dir, "pedigree", "pedigree_parquet")
    ParquetWriter.families_to_parquet(pedigree, output_filename)
    return output_filename


def build_variants_loader_pipeline(
    variants_loader: Union[DenovoLoader, VcfLoader],
    gpf_instance: GPFInstance
) -> AnnotationPipelineDecorator:
    annotation_pipeline = construct_import_annotation_pipeline(gpf_instance)

    if annotation_pipeline is None:
        return variants_loader

    return AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline
    )
