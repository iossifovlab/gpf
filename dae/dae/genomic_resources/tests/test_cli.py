# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pytest
from dae.utils.fs_utils import find_directory_with_a_file
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME
from dae.genomic_resources.cli import cli_manage, \
    _find_resource
from dae.genomic_resources.testing import \
    setup_directories, build_filesystem_test_repository


@pytest.fixture
def repo_fixture(tmp_path_factory):
    path = tmp_path_factory.mktemp("cli_hist_repo_fixture")
    demo_gtf_content = "TP53\tchr3\t300\t200"
    setup_directories(
        path,
        {
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala"
            },
            "sub": {
                "two(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "gene_models": {
                        "genes.txt": demo_gtf_content
                    }
                }
            }
        })
    repo = build_filesystem_test_repository(path)
    return path, repo


def test_cli_manifest(repo_fixture):
    # Given
    path, _repo = repo_fixture
    (path / GR_CONTENTS_FILE_NAME).unlink(missing_ok=True)
    (path / "one" / ".MANIFEST").unlink(missing_ok=True)
    assert not (path / GR_CONTENTS_FILE_NAME).is_file()
    assert not (path / "one" / ".MANIFEST").is_file()

    # When
    cli_manage(["repo-manifest", "-R", str(path)])

    # Then
    assert (path / "one/.MANIFEST").is_file()


def test_cli_without_arguments(repo_fixture, mocker, capsys):
    # Given
    path, _repo = repo_fixture
    cli_manage(["repo-manifest", "-R", str(path)])
    mocker.patch("os.getcwd", return_value=str(path))
    capsys.readouterr()

    # When
    with pytest.raises(SystemExit, match="1"):
        cli_manage([])

        # Then
        out, err = capsys.readouterr()

        assert err == ""
        assert out.startswith("usage: py.test [-h] [--version] [--verbose]")


def test_cli_list(repo_fixture, capsys):
    path, _repo = repo_fixture

    cli_manage(["list", "-R", str(path)])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Basic                0        2 7.0 B        manage one\n" \
        "gene_models          1.0      2 50.0 B       manage sub/two\n"


def test_cli_list_without_repo_argument(repo_fixture, capsys, mocker):
    # Given
    path, _repo = repo_fixture
    cli_manage(["repo-manifest", "-R", str(path)])
    mocker.patch("os.getcwd", return_value=str(path))
    capsys.readouterr()

    # When
    cli_manage(["list"])

    # Then
    out, err = capsys.readouterr()
    assert err == ""
    assert out == \
        f"working with repository: {str(path)}\n" \
        "Basic                0        2 7.0 B        manage one\n" \
        "gene_models          1.0      2 50.0 B       manage sub/two\n"


def test_find_repo_dir_simple(repo_fixture):
    # Given
    path, _repo = repo_fixture
    (path / GR_CONTENTS_FILE_NAME).unlink(missing_ok=True)
    (path / "one" / ".MANIFEST").unlink(missing_ok=True)
    os.chdir(path)
    res = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    assert res is None

    # When
    cli_manage(["repo-manifest", "-R", str(path)])
    res = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)

    # Then
    assert res == path


def test_find_resource_dir_simple(repo_fixture):
    path, _repo = repo_fixture

    cli_manage(["repo-manifest", "-R", str(path)])
    os.chdir(path / "sub" / "two(1.0)" / "gene_models")

    repo_dir = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    assert repo_dir == path

    resource_dir = find_directory_with_a_file(GR_CONF_FILE_NAME)
    assert resource_dir == path / "sub" / "two(1.0)"

    path = pathlib.Path(resource_dir)
    assert str(path.relative_to(repo_dir)) == "sub/two(1.0)"


def test_find_resource_with_version(repo_fixture):
    path, repo = repo_fixture

    cli_manage(["repo-manifest", "-R", str(path)])
    os.chdir(path / "sub" / "two(1.0)" / "gene_models")

    res = _find_resource(repo.proto, str(path))
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_find_resource_without_version(repo_fixture):
    path, repo = repo_fixture

    cli_manage(["repo-manifest", "-R", str(path)])
    os.chdir(path / "one")

    res = _find_resource(repo.proto, str(path))
    assert res.resource_id == "one"
    assert res.version == (0,)


def test_find_resource_with_resource_id(repo_fixture):
    path, repo = repo_fixture

    res = _find_resource(
        repo.proto, str(path), resource="sub/two")
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_repo_init(repo_fixture):
    # Given
    path, _repo = repo_fixture
    (path / GR_CONTENTS_FILE_NAME).unlink(missing_ok=True)

    # When
    cli_manage(["repo-init", "-R", str(path)])

    # Then
    assert (path / ".CONTENTS").exists()


def test_repo_init_inside_repo(repo_fixture):
    # Given
    path, _repo = repo_fixture
    (path / GR_CONTENTS_FILE_NAME).unlink(missing_ok=True)
    (path / "inside").mkdir()
    cli_manage(["repo-init", "-R", str(path)])

    # When
    with pytest.raises(SystemExit, match="1"):
        cli_manage(["repo-init", "-R", str(path / "inside")])

    # Then
    assert not (path / "inside" / ".CONTENTS").exists()
