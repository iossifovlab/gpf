# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Any

import pytest
import toml
import yaml

from gpf.gpf_instance.adjustments.gpf_instance_adjustments import (
    EnableDisableStudies,
    cli,
)


def _write_instance(
    root: pathlib.Path,
    visible_datasets: list[str] | None = None,
) -> pathlib.Path:
    config: dict[str, Any] = {
        "instance_id": "test_enable_disable",
        "reference_genome": {
            "resource_id": "hg38/genomes/GRCh38-hg38",
        },
        "gene_models": {
            "resource_id": "hg38/gene_models/refGene_v20170601",
        },
    }
    if visible_datasets is not None:
        config["gpfjs"] = {"visible_datasets": visible_datasets}
    config_file = root / "gpf_instance.yaml"
    config_file.write_text(yaml.safe_dump(config), encoding="utf8")
    return config_file


def _write_toml(path: pathlib.Path, config: dict[str, Any]) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(toml.dumps(config), encoding="utf8")
    return path


def _write_yaml(path: pathlib.Path, config: dict[str, Any]) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config), encoding="utf8")
    return path


def _visible_datasets(root: pathlib.Path) -> Any:
    config = yaml.safe_load(
        (root / "gpf_instance.yaml").read_text(encoding="utf8"))
    return config["gpfjs"].get("visible_datasets")


def test_disable_studies_disables_matching_toml_study(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    study = _write_toml(
        tmp_path / "studies" / "s1" / "s1.conf", {"id": "s1"})

    cli(["-i", str(tmp_path), "disable-studies", "s1"])

    assert toml.loads(study.read_text(encoding="utf8")) == {
        "id": "s1", "enabled": False,
    }


def test_disable_studies_leaves_other_toml_study_unchanged(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    study = _write_toml(
        tmp_path / "studies" / "s2" / "s2.conf", {"id": "s2"})

    cli(["-i", str(tmp_path), "disable-studies", "s1"])

    assert toml.loads(study.read_text(encoding="utf8")) == {"id": "s2"}


def test_enable_studies_enables_matching_yaml_study(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    study = _write_yaml(
        tmp_path / "studies" / "s1" / "s1.yaml",
        {"id": "s1", "enabled": False})

    cli(["-i", str(tmp_path), "enable-studies", "s1"])

    assert yaml.safe_load(study.read_text(encoding="utf8")) == {
        "id": "s1", "enabled": True,
    }


def test_disable_studies_adjusts_toml_dataset(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    dataset = _write_toml(
        tmp_path / "datasets" / "ds1" / "ds1.conf",
        {"id": "ds1", "studies": ["s1", "s2"]})

    cli(["-i", str(tmp_path), "disable-studies", "ds1", "s1"])

    assert toml.loads(dataset.read_text(encoding="utf8")) == {
        "id": "ds1", "studies": ["s2"], "enabled": False,
    }


def test_disable_studies_removes_study_from_other_yaml_dataset(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    dataset = _write_yaml(
        tmp_path / "datasets" / "ds2" / "ds2.yaml",
        {"id": "ds2", "studies": ["s1", "s2"]})

    cli(["-i", str(tmp_path), "disable-studies", "s1"])

    assert yaml.safe_load(dataset.read_text(encoding="utf8")) == {
        "id": "ds2", "studies": ["s2"],
    }


def test_enable_studies_also_removes_study_from_dataset(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    dataset = _write_yaml(
        tmp_path / "datasets" / "ds1" / "ds1.yaml",
        {"id": "ds1", "studies": ["s1", "s2"]})

    cli(["-i", str(tmp_path), "enable-studies", "s1"])

    assert yaml.safe_load(dataset.read_text(encoding="utf8")) == {
        "id": "ds1", "studies": ["s2"],
    }


def test_study_is_matched_by_config_id_not_by_file_name(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    matching = _write_toml(
        tmp_path / "studies" / "dir_a" / "file_a.conf", {"id": "s1"})
    other = _write_toml(
        tmp_path / "studies" / "s1" / "s1.conf", {"id": "s2"})

    cli(["-i", str(tmp_path), "disable-studies", "s1"])

    assert toml.loads(matching.read_text(encoding="utf8")) == {
        "id": "s1", "enabled": False,
    }
    assert toml.loads(other.read_text(encoding="utf8")) == {"id": "s2"}


def test_dataset_is_matched_by_config_id_not_by_file_name(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    matching = _write_yaml(
        tmp_path / "datasets" / "dir_a" / "file_a.yaml",
        {"id": "ds1", "studies": []})
    other = _write_yaml(
        tmp_path / "datasets" / "ds1" / "ds1.yaml",
        {"id": "ds2", "studies": []})

    cli(["-i", str(tmp_path), "disable-studies", "ds1"])

    assert yaml.safe_load(matching.read_text(encoding="utf8")) == {
        "id": "ds1", "studies": [], "enabled": False,
    }
    assert yaml.safe_load(other.read_text(encoding="utf8")) == {
        "id": "ds2", "studies": [],
    }


def test_dataset_without_studies_key_raises_key_error(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)
    _write_yaml(tmp_path / "datasets" / "ds1" / "ds1.yaml", {"id": "ds1"})
    cmd = EnableDisableStudies(str(tmp_path), {"ds1"}, enabled=False)

    with pytest.raises(KeyError, match="studies"):
        cmd.execute()


def test_enable_studies_appends_missing_visible_datasets(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path, visible_datasets=["a", "b"])

    cli(["-i", str(tmp_path), "enable-studies", "b"])
    cli(["-i", str(tmp_path), "enable-studies", "c"])

    assert _visible_datasets(tmp_path) == ["a", "b", "c"]


def test_disable_studies_removes_visible_datasets(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path, visible_datasets=["a", "b", "c"])

    cli(["-i", str(tmp_path), "disable-studies", "b", "x"])

    assert _visible_datasets(tmp_path) == ["a", "c"]


def test_enable_studies_keeps_empty_visible_datasets_empty(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path, visible_datasets=[])

    cli(["-i", str(tmp_path), "enable-studies", "a"])

    assert _visible_datasets(tmp_path) == []


def test_enable_studies_without_visible_datasets_adds_none(
    tmp_path: pathlib.Path,
) -> None:
    _write_instance(tmp_path)

    cli(["-i", str(tmp_path), "enable-studies", "a"])

    assert _visible_datasets(tmp_path) is None


@pytest.mark.parametrize("method", ["_execute_studies", "_execute_datasets"])
def test_unknown_config_format_raises_value_error(
    tmp_path: pathlib.Path, method: str,
) -> None:
    _write_instance(tmp_path)
    cmd = EnableDisableStudies(str(tmp_path), {"s1"})

    with pytest.raises(ValueError, match="unknown config format json"):
        getattr(cmd, method)(config_format="json")


@pytest.mark.parametrize("method", ["_execute_studies", "_execute_datasets"])
def test_default_config_format_is_toml(
    tmp_path: pathlib.Path, method: str,
) -> None:
    _write_instance(tmp_path)
    subdir = "studies" if method == "_execute_studies" else "datasets"
    conf = _write_toml(
        tmp_path / subdir / "s1.conf", {"id": "s1", "studies": []})
    yaml_conf = _write_yaml(
        tmp_path / subdir / "s1.yaml", {"id": "s1", "studies": []})
    cmd = EnableDisableStudies(str(tmp_path), {"s1"}, enabled=True)

    getattr(cmd, method)()

    assert toml.loads(conf.read_text(encoding="utf8"))["enabled"] is True
    assert "enabled" not in yaml.safe_load(
        yaml_conf.read_text(encoding="utf8"))


def test_cli_without_instance_exits_with_code_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DAE_DB_DIR", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        cli(["enable-studies", "s1"])

    assert excinfo.value.code == 1


def test_cli_uses_dae_db_dir_when_instance_is_missing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_instance(tmp_path)
    study = _write_toml(tmp_path / "studies" / "s1.conf", {"id": "s1"})
    monkeypatch.setenv("DAE_DB_DIR", str(tmp_path))

    cli(["disable-studies", "s1"])

    assert toml.loads(study.read_text(encoding="utf8"))["enabled"] is False


def test_cli_help_exits_with_code_0() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli(["--help"])

    assert excinfo.value.code == 0


def test_cli_unknown_option_exits_with_code_2() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli(["--no-such-option"])

    assert excinfo.value.code == 2
