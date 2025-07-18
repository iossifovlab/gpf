# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import pytest
import pytest_mock
from dae.utils import fs_utils


@pytest.mark.parametrize("segments, expected", [
    (["/abc", "de"], "/abc/de"),
    (["ab", "c"], "ab/c"),
    (["s3://server/", "path"], "s3://server/path"),
    (["/abc/", "s3://server/", "path"], "s3://server/path"),
    (["s3://server/", "/abc/", "path"], "/abc/path"),
])
def test_join(
    segments: str,
    expected: str,
) -> None:
    assert fs_utils.join(*segments) == expected


@pytest.mark.parametrize("url, expected", [
    ("/filename", "/"),
    ("/dir/filename", "/dir"),
    ("file:///dir/filename", "file:///dir"),
    ("s3://bucket", "s3://"),
    ("s3://bucket/dir/filename", "s3://bucket/dir"),
    ("file", None),  # None signifies cwd
    ("", ""),
    ("/", "/"),
    ("s3://", "s3://"),
])
def test_containing_path(
    url: str,
    expected: str | None,
) -> None:
    expected = expected if expected is not None else os.getcwd()
    assert fs_utils.containing_path(url) == expected


@pytest.mark.parametrize("filename, exists_mockery, expected", [
    ("test", {"test": True, "test.tbi": True}, "test.tbi"),
    ("test", {"test": True, "test.csi": True}, "test.csi"),
    ("test", {"test": True}, None),
])
def test_tabix_index_filename(
    mocker: pytest_mock.MockFixture,
    filename: str,
    exists_mockery: dict[str, bool],
    expected: str | None,
) -> None:
    mocker.patch(
        "dae.utils.fs_utils.exists",
        lambda tf: exists_mockery.get(tf, False))
    assert fs_utils.tabix_index_filename(filename) == expected


def test_tabix_index_filename_file_not_found(
    mocker: pytest_mock.MockFixture,
) -> None:
    mocker.patch(
        "dae.utils.fs_utils.exists",
        return_value=False)
    with pytest.raises(IOError, match="tabix file 'test' not found"):
        fs_utils.tabix_index_filename("test")


@pytest.mark.parametrize("url, expected", [
    ("/filename", "/filename"),
    ("/dir/filename", "/dir/filename"),
    ("file:///dir/filename", "file:///dir/filename"),
    ("s3://bucket", "s3://bucket"),
    ("s3://bucket/dir/filename", "s3://bucket/dir/filename"),
    ("file", "/abs/path/file"),
    ("./file", "/abs/path/file"),
    ("/", "/"),
    ("s3://", "s3://"),
])
def test_abspath(
    url: str,
    expected: str,
    mocker: pytest_mock.MockFixture,
) -> None:
    mocker.patch("os.getcwd", return_value="/abs/path")
    res = fs_utils.abspath(url)
    assert res == expected


def test_copy_folder(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    dest_path = tmp_path_factory.mktemp("dest")

    src_path = tmp_path_factory.mktemp("src")
    (src_path / "a").mkdir(parents=True)
    (src_path / "c").mkdir(parents=True)
    (src_path / "a" / "b.txt").write_text("b")
    (src_path / "c" / "d.txt").write_text("d")

    fs_utils.copy(str(dest_path), str(src_path))

    assert (dest_path / "a" / "b.txt").read_text() == "b"
    assert (dest_path / "c" / "d.txt").read_text() == "d"
