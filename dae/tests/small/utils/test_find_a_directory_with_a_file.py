# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest_mock
from dae.genomic_resources.testing import setup_directories
from dae.utils.fs_utils import (
    find_directory_with_a_file,
    find_subdirectories_with_a_file,
)


def test_one_parent(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "file.test": "",
                "dir2": {
                    "dir3": {
                    },
                },
            },
        },
    )
    dirname = find_directory_with_a_file(
        "file.test", str(tmp_path / "dir1" / "dir2"))
    assert dirname == tmp_path / "dir1"


def test_two_parents(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "file.test": "",
                "dir2": {
                    "dir3": {
                    },
                },
            },
        },
    )

    dirname = find_directory_with_a_file(
        "file.test", str(tmp_path / "dir1" / "dir2" / "dir3"))
    assert dirname == tmp_path / "dir1"


def test_first_parent(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "file.test": "",
                "dir2": {
                    "file.test": "",
                    "dir3": {
                    },
                },
            },
        },
    )

    dirname = find_directory_with_a_file(
        "file.test", str(tmp_path / "dir1" / "dir2" / "dir3"))
    assert dirname == tmp_path / "dir1" / "dir2"


def test_one_parent_getcwd(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockFixture,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "file.test": "",
                "dir2": {
                    "dir3": {
                    },
                },
            },
        },
    )
    mocker.patch(
        "os.getcwd",
        return_value=str(tmp_path / "dir1" / "dir2"))

    dirname = find_directory_with_a_file("file.test")
    assert dirname == tmp_path / "dir1"


def test_two_parents_getcwd(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockFixture,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "file.test": "",
                "dir2": {
                    "dir3": {
                    },
                },
            },
        },
    )
    mocker.patch(
        "os.getcwd",
        return_value=str(tmp_path / "dir1" / "dir2" / "dir3"))

    dirname = find_directory_with_a_file("file.test")
    assert dirname == tmp_path / "dir1"


def test_first_parent_getcwd(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockFixture,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "file.test": "",
                "dir2": {
                    "file.test": "",
                    "dir3": {
                    },
                },
            },
        },
    )

    mocker.patch(
        "os.getcwd",
        return_value=str(tmp_path / "dir1" / "dir2" / "dir3"))
    dirname = find_directory_with_a_file("file.test")
    assert dirname == tmp_path / "dir1" / "dir2"


def test_subdirectories_with_a_file(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockFixture,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "dir2": {
                    "file.test": "",
                    "dir3": {
                    },
                },
                "dir4": {
                    "file.test": "",
                    "dir5": {
                    },
                },
            },
        },
    )

    mocker.patch(
        "os.getcwd",
        return_value=str(tmp_path / "dir1"))
    dirname = find_subdirectories_with_a_file("file.test")
    assert set(dirname) == {
        tmp_path / "dir1" / "dir2",
        tmp_path / "dir1" / "dir4"}


def test_subdirectories_with_a_file2(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "dir2": {
                    "dir3": {
                        "file.test": "",
                    },
                },
                "dir4": {
                    "dir5": {
                        "file.test": "",
                    },
                },
            },
        },
    )

    dirname = find_subdirectories_with_a_file("file.test", tmp_path / "dir1")
    assert set(dirname) == {
        tmp_path / "dir1" / "dir2" / "dir3",
        tmp_path / "dir1" / "dir4" / "dir5",
    }


def test_subdirectories_with_a_file3(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path,
        {
            "dir1": {
                "dir2": {
                    "file.test": "",
                    "dir3": {
                        "file.test": "",
                    },
                },
                "dir4": {
                    "dir5": {
                        "file.test": "",
                    },
                },
            },
        },
    )

    dirname = find_subdirectories_with_a_file("file.test", tmp_path / "dir1")
    assert set(dirname) == {
        tmp_path / "dir1" / "dir2",
        tmp_path / "dir1" / "dir2" / "dir3",
        tmp_path / "dir1" / "dir4" / "dir5",
    }
