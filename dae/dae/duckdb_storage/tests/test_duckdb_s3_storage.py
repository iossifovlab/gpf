# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage
from dae.genomic_resources.testing import (
    build_s3_test_bucket,
    build_s3_test_filesystem,
    s3_test_server_endpoint,
)
from dae.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture(scope="session")
def duckdb_storage_config(tmp_path_factory: pytest.TempPathFactory) -> dict:
    s3_endpoint = s3_test_server_endpoint()
    s3_filesystem = build_s3_test_filesystem(s3_endpoint)
    s3_test_bucket = build_s3_test_bucket(s3_filesystem)
    root_path = tmp_path_factory.mktemp("duckdb_storage_work_dir_s3")

    return {
        "id": "dev_duckdb_storage",
        "storage_type": "duckdb2",
        "db": "duckdb_storage/dev_storage.db",
        "base_dir": s3_test_bucket,
        "endpoint_url": s3_endpoint,
        "work_dir": str(root_path),
    }


@pytest.fixture(scope="session")
def duckdb_storage_fixture(
        duckdb_storage_config: dict) -> DuckDbGenotypeStorage:
    storage_factory = get_genotype_storage_factory("duckdb")
    assert storage_factory is not None
    storage = storage_factory(duckdb_storage_config)
    assert storage is not None
    assert isinstance(storage, DuckDbGenotypeStorage)
    return storage


@pytest.fixture(scope="session")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        duckdb_storage_fixture: DuckDbGenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{duckdb_storage_fixture.storage_id}")
    gpf_instance = foobar_gpf(root_path, duckdb_storage_fixture)
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
        gpf_instance)


def test_duckdb_s3_storage(
    duckdb_storage_fixture: DuckDbGenotypeStorage,
) -> None:
    assert duckdb_storage_fixture is not None
    assert duckdb_storage_fixture.connection_factory is None


def test_import_storage(
    imported_study: GenotypeData,
) -> None:
    assert imported_study is not None
