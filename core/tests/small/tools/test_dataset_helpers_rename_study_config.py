# pylint: disable=C0114,C0115,C0116
import logging
import pathlib
from typing import Any, cast

import pytest
import toml
from box import Box

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.tools.dataset_helpers import DatasetHelpers


class StubGPFInstance:
    """Answer `get_genotype_data_config` from a fixed map of dataset ids."""

    def __init__(self, conf_dirs: dict[str, pathlib.Path]) -> None:
        self.conf_dirs = conf_dirs
        self.reload_calls = 0

    def get_genotype_data_config(self, dataset_id: str) -> Box | None:
        conf_dir = self.conf_dirs.get(dataset_id)
        if conf_dir is None:
            return None
        return Box({"conf_dir": str(conf_dir)})

    def reload(self) -> None:
        self.reload_calls += 1


def make_study_dir(root: pathlib.Path, name: str) -> pathlib.Path:
    study_dir = root / name
    study_dir.mkdir()
    (study_dir / f"{name}.conf").write_text('id = "old"\n')
    return study_dir


def make_helpers(conf_dirs: dict[str, pathlib.Path]) -> DatasetHelpers:
    return DatasetHelpers(cast(GPFInstance, StubGPFInstance(conf_dirs)))


def tree(root: pathlib.Path) -> list[str]:
    return sorted(
        str(path.relative_to(root)) for path in root.rglob("*"))


NEW_CONFIG: dict[str, Any] = {"id": "new_study", "name": "New"}


def test_default_dry_run_moves_backup_into_new_directory(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    helpers = make_helpers({"old_study": study_dir})

    helpers.rename_study_config("old_study", "new_study", NEW_CONFIG)

    assert tree(tmp_path) == [
        "new_study",
        "new_study/new_study.conf",
        "new_study/old_study.conf_bak",
    ]


def test_explicit_false_dry_run_renames_the_config_directory(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    helpers = make_helpers({"old_study": study_dir})

    helpers.rename_study_config(
        "old_study", "new_study", NEW_CONFIG, dry_run=False)

    assert not study_dir.exists()
    assert (tmp_path / "new_study").is_dir()


def test_backup_keeps_the_old_config_content(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    helpers = make_helpers({"old_study": study_dir})

    helpers.rename_study_config(
        "old_study", "new_study", NEW_CONFIG, dry_run=False)

    backup = tmp_path / "new_study" / "old_study.conf_bak"
    assert backup.read_text() == 'id = "old"\n'


def test_new_config_file_holds_toml_dump_of_config_content(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    helpers = make_helpers({"old_study": study_dir})

    helpers.rename_study_config(
        "old_study", "new_study", NEW_CONFIG, dry_run=False)

    new_config = tmp_path / "new_study" / "new_study.conf"
    assert new_config.read_text() == toml.dumps(NEW_CONFIG)


def test_new_config_file_is_named_after_new_id_not_old_file(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = tmp_path / "old_study"
    study_dir.mkdir()
    (study_dir / "other_name.conf").write_text('id = "old"\n')
    helpers = make_helpers({"old_study": study_dir})

    helpers.rename_study_config(
        "old_study", "new_study", NEW_CONFIG, dry_run=False)

    assert tree(tmp_path) == [
        "new_study",
        "new_study/new_study.conf",
        "new_study/other_name.conf_bak",
    ]


def test_true_dry_run_changes_no_file(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    helpers = make_helpers({"old_study": study_dir})

    helpers.rename_study_config(
        "old_study", "new_study", NEW_CONFIG, dry_run=True)

    assert tree(tmp_path) == ["old_study", "old_study/old_study.conf"]
    assert (study_dir / "old_study.conf").read_text() == 'id = "old"\n'


def test_true_dry_run_logs_the_three_steps(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    helpers = make_helpers({"old_study": study_dir})
    new_dir = tmp_path / "new_study"

    with caplog.at_level(logging.INFO, logger="gpf.tools.dataset_helpers"):
        helpers.rename_study_config(
            "old_study", "new_study", NEW_CONFIG, dry_run=True)

    assert caplog.messages == [
        f"going to disable config file {study_dir / 'old_study.conf'}",
        f"going to rename config directory {study_dir} to {new_dir}",
        f"going to create a new config file {new_dir / 'new_study.conf'}",
    ]


def test_unknown_dataset_changes_no_file(
    tmp_path: pathlib.Path,
) -> None:
    study_dir = make_study_dir(tmp_path, "old_study")
    stub = StubGPFInstance({"old_study": study_dir})
    helpers = DatasetHelpers(cast(GPFInstance, stub))

    helpers.rename_study_config("missing", "new_study", NEW_CONFIG)

    assert tree(tmp_path) == ["old_study", "old_study/old_study.conf"]
    assert stub.reload_calls == 1
