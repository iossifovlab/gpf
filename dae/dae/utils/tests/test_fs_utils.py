# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest
from dae.utils import fs_utils


@pytest.mark.parametrize("segments, expected", [
    (["/abc", "de"], "/abc/de"),
    (["ab", "c"], "ab/c"),
    (["s3://server/", "path"], "s3://server/path"),
    (["/abc/", "s3://server/", "path"], "s3://server/path"),
    (["s3://server/", "/abc/", "path"], "/abc/path"),
])
def test_join(segments, expected):
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
def test_containing_path(url, expected):
    expected = expected if expected is not None else os.getcwd()
    assert fs_utils.containing_path(url) == expected
