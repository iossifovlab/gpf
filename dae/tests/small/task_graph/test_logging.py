# pylint: disable=C0114,C0115,C0116,W0212
import logging
import os
from pathlib import Path

import pytest
from dae.task_graph.logging import (
    FsspecHandler,
    configure_task_logging,
    ensure_log_dir,
    safe_task_id,
)


def test_ensure_log_dir_creates_directory(tmp_path: Path) -> None:
    log_dir = tmp_path / "nested"
    result = ensure_log_dir(task_log_dir=str(log_dir))

    assert result == str(log_dir)
    assert os.path.isdir(result)


def test_ensure_log_dir_defaults_to_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(str(tmp_path))
    result = ensure_log_dir()

    expected = os.path.join(str(tmp_path), ".task-log")
    assert result == expected
    assert os.path.isdir(result)


def test_safe_task_id_replaces_invalid_characters() -> None:
    raw = "task 1/2,3:4-(5);6"
    assert safe_task_id(raw) == "task_1_2_3_4__5__6"


def test_safe_task_id_truncates_long_ids() -> None:
    long_id = "x" * 210
    sanitized = safe_task_id(long_id)

    assert len(sanitized) <= 200
    assert sanitized.startswith("x" * 150)
    assert sanitized[150] == "_"


def test_configure_task_logging_returns_null_handler() -> None:
    handler = configure_task_logging(None, "task", 1)
    assert isinstance(handler, logging.NullHandler)


def test_configure_task_logging_writes_to_log_file(tmp_path: Path) -> None:
    handler = configure_task_logging(str(tmp_path), "task", 1)
    assert isinstance(handler, FsspecHandler)
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        handler.handle(record)
    finally:
        handler.close()

    log_file = tmp_path / "log_task.log"
    assert log_file.exists()
    assert "hello world" in log_file.read_text()


def test_configure_task_logging_sets_levels(tmp_path: Path) -> None:
    handler_warning = configure_task_logging(str(tmp_path), "warn", 0)
    handler_info = configure_task_logging(str(tmp_path), "info", 1)
    handler_debug = configure_task_logging(str(tmp_path), "debug", 2)

    try:
        assert handler_warning.level == logging.WARNING
        assert handler_info.level == logging.INFO
        assert handler_debug.level == logging.DEBUG
    finally:
        handler_warning.close()
        handler_info.close()
        handler_debug.close()
