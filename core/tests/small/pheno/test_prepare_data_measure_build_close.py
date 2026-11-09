# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gc
import shutil
from collections.abc import Generator
from pathlib import Path

import duckdb
import pytest

from gpf.pheno.pheno_data import PhenotypeStudy
from gpf.pheno.prepare_data import PreparePhenoBrowserBase
from gpf.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry


@pytest.fixture
def no_gc() -> Generator[None, None, None]:
    gc.disable()
    yield
    gc.enable()


@pytest.mark.usefixtures("no_gc")
def test_do_measure_build_releases_the_pheno_db_file(
    tmp_path: Path,
    fake_pheno_db_dir: Path,
) -> None:
    pheno_dir = tmp_path / "pheno"
    shutil.copytree(fake_pheno_db_dir / "fake", pheno_dir / "fake")
    dbfile = pheno_dir / "fake" / "fake.db"
    storage_registry = PhenotypeStorageRegistry()
    storage_registry.register_default_storage(
        PhenotypeStorage.from_config(
            {"id": "copy_storage", "base_dir": pheno_dir},
        ),
    )
    study = PhenotypeStudy("fake", str(dbfile))
    measure = study.get_measure("i1.m5")
    study.close()

    PreparePhenoBrowserBase.do_measure_build(
        "fake", measure, storage_registry, str(tmp_path / "images"),
        {}, str(pheno_dir), str(tmp_path / "cache"),
    )

    with duckdb.connect(dbfile, read_only=False) as conn:
        assert conn.execute("SELECT 1").fetchone() == (1,)
