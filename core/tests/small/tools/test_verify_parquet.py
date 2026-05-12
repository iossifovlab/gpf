# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import json
import logging
import pathlib

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from gpf.tools.verify_parquet import FileResult, main, verify_parquet_file


@pytest.fixture
def valid_parquet(tmp_path: pathlib.Path) -> pathlib.Path:
    table = pa.table({"x": [1, 2, 3], "y": ["a", "b", "c"]})
    path = tmp_path / "valid.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture
def multi_rowgroup_parquet(tmp_path: pathlib.Path) -> pathlib.Path:
    table = pa.table({
        "x": list(range(1000)),
        "y": ["payload" * 20] * 1000,
    })
    path = tmp_path / "multi.parquet"
    pq.write_table(table, path, row_group_size=100, compression="snappy")
    return path


def test_verify_parquet_file_valid_returns_ok(
    valid_parquet: pathlib.Path,
) -> None:
    result = verify_parquet_file(str(valid_parquet))

    assert isinstance(result, FileResult)
    assert result.ok is True
    assert result.path == str(valid_parquet)
    assert result.error_class is None
    assert result.message is None
    assert result.row_group is None


def test_verify_parquet_file_zero_byte_returns_failure(
    tmp_path: pathlib.Path,
) -> None:
    empty = tmp_path / "empty.parquet"
    empty.touch()

    result = verify_parquet_file(str(empty))

    assert result.ok is False
    assert result.path == str(empty)
    assert result.error_class is not None
    assert result.message
    assert result.row_group is None


def test_verify_parquet_file_truncated_returns_failure(
    valid_parquet: pathlib.Path,
) -> None:
    # Simulate a writer that died mid-flush: keep first 100 bytes only.
    full = valid_parquet.read_bytes()
    assert len(full) > 100
    valid_parquet.write_bytes(full[:100])

    result = verify_parquet_file(str(valid_parquet))

    assert result.ok is False
    assert result.error_class is not None
    assert result.message
    assert result.row_group is None


def test_verify_parquet_file_text_content_returns_failure(
    tmp_path: pathlib.Path,
) -> None:
    fake = tmp_path / "fake.parquet"
    fake.write_text("this is plainly not a parquet file\n")

    result = verify_parquet_file(str(fake))

    assert result.ok is False
    assert result.error_class is not None
    assert result.message
    assert result.row_group is None


def test_verify_parquet_file_deep_catches_data_page_corruption(
    multi_rowgroup_parquet: pathlib.Path,
) -> None:
    raw = bytearray(multi_rowgroup_parquet.read_bytes())
    # Flip bytes well inside the data region; footer at file tail stays intact.
    offset = len(raw) // 4
    for i in range(offset, offset + 32):
        raw[i] ^= 0xFF
    multi_rowgroup_parquet.write_bytes(bytes(raw))

    shallow = verify_parquet_file(str(multi_rowgroup_parquet), deep=False)
    assert shallow.ok is True, (
        "shallow check should pass: footer intact, data page corrupt"
    )

    deep = verify_parquet_file(str(multi_rowgroup_parquet), deep=True)
    assert deep.ok is False
    assert deep.error_class is not None
    assert deep.message
    assert deep.row_group is not None
    assert deep.row_group >= 0


def test_cli_single_valid_file_exits_zero(
    valid_parquet: pathlib.Path,
) -> None:
    assert main([str(valid_parquet)]) == 0


def test_cli_nonexistent_path_exits_two(tmp_path: pathlib.Path) -> None:
    ghost = tmp_path / "does-not-exist.parquet"
    assert main([str(ghost)]) == 2


def test_cli_directory_recursion_finds_nested_files(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    table = pa.table({"x": [1, 2, 3]})
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    pq.write_table(table, tmp_path / "a" / "x.parquet")
    pq.write_table(table, tmp_path / "a" / "b" / "y.parquet")
    # Distractors that must not be checked.
    (tmp_path / "a" / "README.md").write_text("ignore me\n")
    (tmp_path / "a" / "notes.txt").write_text("ignore me too\n")

    with caplog.at_level(logging.INFO, logger="verify_parquet"):
        rc = main([str(tmp_path)])

    assert rc == 0
    summary = [r for r in caplog.records if "Checked" in r.message]
    assert summary
    assert "Checked 2 files" in summary[-1].message


def test_cli_skips_dotfiles_and_dotdirs(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    table = pa.table({"x": [1]})
    pq.write_table(table, tmp_path / "real.parquet")
    # Dotfiles and dot-directories are stray artefacts from interrupted
    # writes / OS metadata. They must not fail the run.
    (tmp_path / ".tmp.parquet").write_bytes(b"garbage")
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "stale.parquet").write_bytes(b"garbage")

    with caplog.at_level(logging.INFO, logger="verify_parquet"):
        rc = main([str(tmp_path)])

    assert rc == 0
    summary = [r for r in caplog.records if "Checked" in r.message]
    assert summary
    assert "Checked 1 files" in summary[-1].message


def test_cli_json_report_shape(
    valid_parquet: pathlib.Path, tmp_path: pathlib.Path,
) -> None:
    bad = tmp_path / "bad.parquet"
    bad.write_bytes(b"")
    report = tmp_path / "report.json"

    rc = main([
        str(valid_parquet), str(bad),
        "--json", str(report),
    ])
    assert rc == 1

    doc = json.loads(report.read_text())
    assert doc["tool"] == "verify_parquet"
    assert doc["deep"] is False
    assert doc["checked"] == 2
    assert doc["failures"] == 1
    assert {entry["path"] for entry in doc["files"]} == {
        str(valid_parquet), str(bad),
    }
    by_path = {entry["path"]: entry for entry in doc["files"]}
    assert by_path[str(valid_parquet)]["ok"] is True
    assert by_path[str(bad)]["ok"] is False
    assert by_path[str(bad)]["error_class"]
    assert by_path[str(bad)]["message"]


def test_cli_jobs_flag_runs_to_completion(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    table = pa.table({"x": [1, 2, 3]})
    for i in range(5):
        pq.write_table(table, tmp_path / f"f{i}.parquet")
    # Sprinkle in a broken file so we exercise both paths concurrently.
    (tmp_path / "broken.parquet").write_bytes(b"")

    with caplog.at_level(logging.INFO, logger="verify_parquet"):
        rc = main([str(tmp_path), "-j", "2"])

    assert rc == 1
    summary = [r for r in caplog.records if "Checked" in r.message]
    assert summary
    assert "Checked 6 files, 1 failures" in summary[-1].message


def test_cli_empty_directory_exits_two(tmp_path: pathlib.Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    assert main([str(empty_dir)]) == 2


def test_cli_mixed_good_and_bad_exits_one(
    valid_parquet: pathlib.Path, tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bad = tmp_path / "bad.parquet"
    bad.write_bytes(b"")

    with caplog.at_level(logging.ERROR, logger="verify_parquet"):
        rc = main([str(valid_parquet), str(bad)])

    assert rc == 1
    assert any(
        f"FAIL {bad}" in rec.message
        for rec in caplog.records
        if rec.levelno >= logging.ERROR
    )
