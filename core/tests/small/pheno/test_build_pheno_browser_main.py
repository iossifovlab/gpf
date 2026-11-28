# pylint: disable=W0621,C0114,C0116
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_mock

from gpf.pheno import build_pheno_browser as tool
from gpf.pheno.registry import PhenoRegistry


@pytest.fixture
def build_mock(mocker: pytest_mock.MockerFixture) -> MagicMock:
    return mocker.patch.object(tool, "build_pheno_browser")


@pytest.fixture
def gpfi_build(mocker: pytest_mock.MockerFixture) -> MagicMock:
    instance = MagicMock()
    instance.dae_config = {
        "phenotype_data": {"dir": "/instance/pheno"},
        "phenotype_images": "/instance/images",
    }
    instance.get_pheno_cache_path.return_value = Path("/instance/cache")
    return mocker.patch.object(
        tool.GPFInstance, "build", return_value=instance)


@pytest.fixture
def gpfi(gpfi_build: MagicMock) -> MagicMock:
    instance: MagicMock = gpfi_build.return_value
    return instance


def test_main_help_exits_with_code_0() -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--help"])

    assert excinfo.value.code == 0


def test_main_unknown_option_exits_with_code_2() -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--no-such-option"])

    assert excinfo.value.code == 2


def test_main_reads_sys_argv_when_argv_is_none(
    fake_pheno_db_dir: Path,
    build_mock: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys, "argv",
        ["build_pheno_browser", "fake", "--pheno-db-dir",
         str(fake_pheno_db_dir)],
    )

    result = tool.main()

    assert result == 0
    assert [c.args[2].pheno_id for c in build_mock.call_args_list] == [
        "fake"]


def test_main_pheno_db_dir_one_id_uses_defaults(
    fake_pheno_db_dir: Path,
    build_mock: MagicMock,
) -> None:
    result = tool.main(["fake", "--pheno-db-dir", str(fake_pheno_db_dir)])

    assert result == 0
    build_mock.assert_called_once()
    pheno_db_dir, storage_registry, data, cache_dir, images_dir = \
        build_mock.call_args.args
    assert pheno_db_dir == fake_pheno_db_dir
    assert data.pheno_id == "fake"
    assert cache_dir == fake_pheno_db_dir
    assert images_dir == fake_pheno_db_dir / "images"
    default_storage = storage_registry.get_default_phenotype_storage()
    assert default_storage.storage_id == "default_storage"
    assert default_storage.base_dir == fake_pheno_db_dir


def test_main_pheno_db_dir_passes_regressions_and_cli_kwargs(
    fake_pheno_db_dir: Path,
    build_mock: MagicMock,
) -> None:
    tool.main(["fake", "--pheno-db-dir", str(fake_pheno_db_dir)])

    kwargs = build_mock.call_args.kwargs
    data = build_mock.call_args.args[2]
    assert kwargs["pheno_regressions"] == data.config.get("regressions")
    assert kwargs["pheno_regressions"] is not None
    assert kwargs["phenotype_data_id"] == "fake"
    assert kwargs["storage_dir"] is None
    assert kwargs["gpf_instance"] is None
    assert kwargs["dry_run"] is False
    assert "pheno_db_dir" not in kwargs
    assert "cache_dir" not in kwargs
    assert "images_dir" not in kwargs


def test_main_pheno_db_dir_uses_explicit_storage_cache_and_images(
    fake_pheno_db_dir: Path,
    build_mock: MagicMock,
    tmp_path: Path,
) -> None:
    storage_dir = tmp_path / "storage"
    shutil.copytree(fake_pheno_db_dir, storage_dir)
    cache_dir = tmp_path / "cache"
    images_dir = tmp_path / "images"

    tool.main([
        "fake",
        "--pheno-db-dir", str(fake_pheno_db_dir),
        "--storage-dir", str(storage_dir),
        "--cache-dir", str(cache_dir),
        "--images-dir", str(images_dir),
    ])

    _, storage_registry, data, passed_cache, passed_images = \
        build_mock.call_args.args
    default_storage = storage_registry.get_default_phenotype_storage()
    assert default_storage.base_dir == storage_dir
    assert Path(data.db.dbfile).parent.parent == storage_dir
    assert passed_cache == cache_dir
    assert passed_images == images_dir
    assert build_mock.call_args.kwargs["storage_dir"] == str(storage_dir)


def test_main_pheno_db_dir_without_id_builds_all(
    fake_pheno_db_dir: Path,
    fake_pheno_db: PhenoRegistry,
    build_mock: MagicMock,
) -> None:
    result = tool.main(["--pheno-db-dir", str(fake_pheno_db_dir)])

    assert result == 0
    built = sorted(c.args[2].pheno_id for c in build_mock.call_args_list)
    assert built == sorted(fake_pheno_db.get_phenotype_data_ids())
    assert len(built) > 1


@pytest.mark.usefixtures("build_mock")
def test_main_pheno_db_dir_shuts_down_the_registry(
    fake_pheno_db_dir: Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    shutdown = mocker.spy(PhenoRegistry, "shutdown")

    tool.main(["fake", "--pheno-db-dir", str(fake_pheno_db_dir)])

    shutdown.assert_called_once()


def test_main_gpf_instance_one_id_uses_instance_paths(
    gpfi_build: MagicMock,
    gpfi: MagicMock,
    build_mock: MagicMock,
) -> None:
    data = MagicMock()
    data.config = {"regressions": {"age": {}}}
    gpfi.get_phenotype_data.return_value = data

    result = tool.main(["fake", "--gpf-instance", "/instance/gpf.yaml"])

    assert result == 0
    gpfi_build.assert_called_once_with("/instance/gpf.yaml")
    gpfi.get_phenotype_data.assert_called_once_with("fake")
    gpfi.get_all_phenotype_data.assert_not_called()
    build_mock.assert_called_once()
    assert build_mock.call_args.args == (
        Path("/instance/pheno"),
        gpfi.phenotype_storages,
        data,
        Path("/instance/cache"),
        Path("/instance/images"),
    )
    assert build_mock.call_args.kwargs["pheno_regressions"] == {"age": {}}


def test_main_gpf_instance_without_id_builds_all(
    gpfi_build: MagicMock,
    gpfi: MagicMock,
    build_mock: MagicMock,
) -> None:
    first, second = MagicMock(), MagicMock()
    gpfi.get_all_phenotype_data.return_value = [first, second]

    result = tool.main([])

    assert result == 0
    gpfi_build.assert_called_once_with(None)
    gpfi.get_phenotype_data.assert_not_called()
    assert [c.args[2] for c in build_mock.call_args_list] == [first, second]


def test_main_gpf_instance_shuts_down_the_instance_registry(
    gpfi: MagicMock,
    build_mock: MagicMock,
) -> None:
    gpfi.get_all_phenotype_data.return_value = []

    tool.main([])

    shutdowns = [
        (name, args, kwargs)
        for name, args, kwargs in gpfi.mock_calls
        if name.rsplit(".", 1)[-1] == "shutdown"
    ]
    assert len(shutdowns) == 1
    assert shutdowns[0][1:] == ((), {})
    build_mock.assert_not_called()
