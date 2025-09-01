# pylint: disable=W0621,C0114,C0116,W0212,W0613

from pathlib import Path
from typing import cast

import pytest
from dae.duckdb_storage.duckdb_legacy_genotype_storage import (
    DuckDbLegacyStorage,
)
from dae.genomic_resources.testing import (
    build_s3_test_bucket,
    build_s3_test_filesystem,
    s3_test_server_endpoint,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
    get_genotype_storage_factory,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils import fs_utils


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "duckdb_storage_type" not in metafunc.fixturenames:
        return
    storage_types = [
        "duckdb",
        "duckdb_legacy",
        "duckdb_parquet",
    ]
    if metafunc.config.getoption("enable_s3"):
        storage_types.extend(["duckdb_s3", "duckdb_s3_parquet"])
    metafunc.parametrize(
        "duckdb_storage_type", storage_types, scope="module")


@pytest.fixture(scope="module")
def duckdb_storage_config(
    duckdb_storage_type: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict:
    storage_type = duckdb_storage_type

    if storage_type in {"duckdb", "duckdb_legacy"}:
        storage_path = tmp_path_factory.mktemp(
            f"duckdb_storage_{storage_type}")
        return {
            "id": "dev_duckdb_storage",
            "storage_type": storage_type,
            "db": "storage.db",
            "base_dir": str(storage_path),
        }
    if storage_type == "duckdb_parquet":
        storage_path = tmp_path_factory.mktemp(
            f"duckdb_parquet_{storage_type}")
        return {
            "id": "dev_duckdb_storage",
            "storage_type": "duckdb_parquet",
            "base_dir": str(storage_path),
        }

    assert storage_type in {"duckdb_s3", "duckdb_s3_parquet"}

    s3_endpoint = s3_test_server_endpoint()
    s3_filesystem = build_s3_test_filesystem(s3_endpoint)
    s3_test_bucket = build_s3_test_bucket(s3_filesystem)
    if storage_type == "duckdb_s3_parquet":
        return {
            "id": f"dev_duckdb_storage_{storage_type}",
            "storage_type": "duckdb_s3_parquet",
            "bucket_url": fs_utils.join(s3_test_bucket, "parquet"),
            "endpoint_url": s3_endpoint,
        }
    assert storage_type == "duckdb_s3"
    return {
        "id": f"dev_duckdb_storage_{storage_type}",
        "storage_type": "duckdb_s3",
        "bucket_url": fs_utils.join(s3_test_bucket, "database"),
        "endpoint_url": s3_endpoint,
        "db": "storage.db",
    }


@pytest.fixture(scope="module")
def duckdb_storage_fixture(
    duckdb_storage_config: dict,
) -> GenotypeStorage:
    storage_type = duckdb_storage_config["storage_type"]
    storage_factory = get_genotype_storage_factory(storage_type)
    assert storage_factory is not None
    storage = storage_factory(duckdb_storage_config)
    assert storage is not None
    return storage


@pytest.fixture(scope="module")
def foobar_gpf_fixture(
    tmp_path_factory: pytest.TempPathFactory,
    duckdb_storage_fixture: DuckDbLegacyStorage,
) -> tuple[Path, GPFInstance]:
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{duckdb_storage_fixture.storage_id}")
    gpf_instance = foobar_gpf(root_path, duckdb_storage_fixture)
    return root_path, gpf_instance


@pytest.fixture(scope="module")
def imported_study(
    foobar_gpf_fixture: tuple[Path, GPFInstance],
) -> GenotypeData:
    root_path, gpf_instance = foobar_gpf_fixture
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        foo    13  .  G   C   .    .      .    GT     0/1 0/0 0/1
        foo    14  .  C   T   .    .      .    GT     0/0 0/1 0/1
        """)

    return vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance=gpf_instance)


@pytest.fixture(scope="module")
def foobar_storage_registry(
    foobar_gpf_fixture: tuple[Path, GPFInstance],
) -> GenotypeStorageRegistry:
    _, instance = foobar_gpf_fixture
    return cast(GenotypeStorageRegistry, instance.genotype_storages)
