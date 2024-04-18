# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.testing import setup_directories
from dae.utils.fs_utils import find_directory_with_a_file


def test_one_parent(tmp_path):
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


def test_two_parents(tmp_path):
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


def test_first_parent(tmp_path):
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


def test_one_parent_getcwd(tmp_path, mocker):
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
    mocker.patch("os.getcwd", lambda: str(tmp_path / "dir1" / "dir2"))

    dirname = find_directory_with_a_file("file.test")
    assert dirname == tmp_path / "dir1"


def test_two_parents_getcwd(tmp_path, mocker):
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
    mocker.patch("os.getcwd", lambda: str(tmp_path / "dir1" / "dir2" / "dir3"))

    dirname = find_directory_with_a_file("file.test")
    assert dirname == tmp_path / "dir1"


def test_first_parent_getcwd(tmp_path, mocker):
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

    mocker.patch("os.getcwd", lambda: str(tmp_path / "dir1" / "dir2" / "dir3"))
    dirname = find_directory_with_a_file("file.test")
    assert dirname == tmp_path / "dir1" / "dir2"
