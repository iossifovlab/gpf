# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gc
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any, NoReturn

import duckdb
import pytest

from gpf.pheno.pheno_data import Measure, PhenotypeStudy
from gpf.pheno.prepare_data import PreparePhenoBrowserBase
from gpf.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry


@pytest.fixture
def no_gc() -> Generator[None, None, None]:
    gc.disable()
    yield
    gc.enable()


@pytest.fixture
def pheno_copy(
    tmp_path: Path,
    fake_pheno_db_dir: Path,
) -> tuple[Path, PhenotypeStorageRegistry, Measure]:
    pheno_dir = tmp_path / "pheno"
    shutil.copytree(fake_pheno_db_dir / "fake", pheno_dir / "fake")
    storage_registry = PhenotypeStorageRegistry()
    storage_registry.register_default_storage(
        PhenotypeStorage.from_config(
            {"id": "copy_storage", "base_dir": pheno_dir},
        ),
    )
    study = PhenotypeStudy("fake", str(pheno_dir / "fake" / "fake.db"))
    measure = study.get_measure("i1.m5")
    study.close()
    return pheno_dir, storage_registry, measure


def _do_measure_build(
    tmp_path: Path,
    pheno_copy: tuple[Path, PhenotypeStorageRegistry, Measure],
) -> None:
    pheno_dir, storage_registry, measure = pheno_copy
    PreparePhenoBrowserBase.do_measure_build(
        "fake", measure, storage_registry, str(tmp_path / "images"),
        {}, str(pheno_dir), str(tmp_path / "cache"),
    )


def _assert_read_write_connect_succeeds(dbfile: Path) -> None:
    with duckdb.connect(dbfile, read_only=False) as conn:
        assert conn.execute("SELECT 1").fetchone() == (1,)


@pytest.mark.usefixtures("no_gc")
def test_do_measure_build_releases_the_pheno_db_file(
    tmp_path: Path,
    pheno_copy: tuple[Path, PhenotypeStorageRegistry, Measure],
) -> None:
    _do_measure_build(tmp_path, pheno_copy)

    _assert_read_write_connect_succeeds(pheno_copy[0] / "fake" / "fake.db")


@pytest.mark.usefixtures("no_gc")
def test_do_measure_build_releases_the_pheno_db_file_when_build_raises(
    tmp_path: Path,
    pheno_copy: tuple[Path, PhenotypeStorageRegistry, Measure],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> NoReturn:
        raise RuntimeError("plotting failed")

    monkeypatch.setattr(
        PreparePhenoBrowserBase, "_build_measure", staticmethod(_raise),
    )

    with pytest.raises(RuntimeError, match="plotting failed") as excinfo:
        _do_measure_build(tmp_path, pheno_copy)

    # excinfo keeps the frame of do_measure_build alive, so the registry
    # it made is not freed by reference counting before the connect.
    assert excinfo.tb is not None
    _assert_read_write_connect_succeeds(pheno_copy[0] / "fake" / "fake.db")
