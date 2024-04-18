# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional, cast

import pytest
import pytest_mock

from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage
from dae.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture()
def duckdb_storage_db(
        tmp_path_factory: pytest.TempPathFactory) -> DuckDbGenotypeStorage:
    storage_path = tmp_path_factory.mktemp("duckdb_storage")
    storage_config = {
        "id": "dev_duckdb_storage",
        "storage_type": "duckdb",
        "db": "duckdb_genotype_storage/dev_storage.db",
        "base_dir": storage_path,
    }
    storage_factory = get_genotype_storage_factory("duckdb")
    genotype_storage = cast(
        DuckDbGenotypeStorage, storage_factory(storage_config))
    genotype_storage.start()
    return genotype_storage


@pytest.fixture()
def duckdb_storage_parquet(
        tmp_path_factory: pytest.TempPathFactory) -> DuckDbGenotypeStorage:
    storage_path = tmp_path_factory.mktemp("duckdb_storage")
    storage_config = {
        "id": "dev_duckdb_storage",
        "storage_type": "duckdb",
        "studies_dir": "duckdb_genotype_storage",
        "base_dir": str(storage_path),
    }
    storage_factory = get_genotype_storage_factory("duckdb")
    genotype_storage = cast(
        DuckDbGenotypeStorage, storage_factory(storage_config))
    genotype_storage.start()
    return genotype_storage


def imported_study(
        root_path: pathlib.Path,
        duckdb_storage: DuckDbGenotypeStorage) -> GenotypeData:

    gpf_instance = foobar_gpf(root_path, duckdb_storage)
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

    study = vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)

    return study


@pytest.mark.parametrize(
    "base_dir,parquet_scan,expected",
    [
        ("/test/base/dir", "parquet_scan('aa/bb')",
         "parquet_scan('/test/base/dir/aa/bb')"),
        (None, "parquet_scan('aa/bb')",
         "parquet_scan('aa/bb')"),
        ("/test/base/dir", "parquet_scan('/aa/bb')",
         "parquet_scan('/aa/bb')"),
        ("/test/base/dir", None,
         None),
        ("/test/base/dir", "ala_bala",
         "ala_bala"),
    ],
)
def test_base_dir_join_parquet_scan(
        base_dir: Optional[str], parquet_scan: str, expected: str,
        duckdb_storage_parquet: DuckDbGenotypeStorage,
        mocker: pytest_mock.MockerFixture) -> None:

    mocker.patch.object(
        duckdb_storage_parquet,
        "get_base_dir",
        return_value=base_dir,
    )
    res = duckdb_storage_parquet\
        ._base_dir_join_parquet_scan_or_table(parquet_scan)
    assert res == expected


def test_parquet_storage(
        tmp_path_factory: pytest.TempPathFactory,
        duckdb_storage_parquet: DuckDbGenotypeStorage) -> None:

    root_path = tmp_path_factory.mktemp("test_parquet_storage")
    study = imported_study(root_path, duckdb_storage_parquet)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 2
