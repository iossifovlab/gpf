# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pytest
from dae.utils.fs_utils import find_directory_with_a_file
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME
from dae.genomic_resources.cli import cli_manage, \
    _find_resource
from dae.genomic_resources.testing import build_testing_repository


@pytest.fixture
def repo_fixture(tmp_path):
    demo_gtf_content = "TP53\tchr3\t300\t200".encode("utf-8")
    repo = build_testing_repository(
        scheme="file",
        root_path=str(tmp_path),
        content={
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
    return repo


def test_cli_manifest(repo_fixture, tmp_path):

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).is_file()
    cli_manage(["repo-manifest", "-R", str(tmp_path)])
    assert (tmp_path / "one/.MANIFEST").is_file()


def test_cli_list(repo_fixture, tmp_path, capsys):

    cli_manage(["list", "-R", str(tmp_path)])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Basic                0        2            7 one\n" \
        "gene_models          1.0      2           50 sub/two\n"


def test_find_repo_dir_simple(repo_fixture, tmp_path):
    os.chdir(tmp_path)
    res = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    assert res is None

    cli_manage(["repo-manifest", "-R", str(tmp_path)])

    res = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    assert res == str(tmp_path)


def test_find_resource_dir_simple(repo_fixture, tmp_path):

    cli_manage(["repo-manifest", "-R", str(tmp_path)])
    os.chdir(tmp_path / "sub" / "two(1.0)" / "gene_models")

    repo_dir = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    assert repo_dir == str(tmp_path)

    resource_dir = find_directory_with_a_file(GR_CONF_FILE_NAME)
    assert resource_dir == str(tmp_path / "sub" / "two(1.0)")

    path = pathlib.Path(resource_dir)
    assert str(path.relative_to(repo_dir)) == "sub/two(1.0)"


def test_find_resource_with_version(repo_fixture, tmp_path):

    cli_manage(["repo-manifest", "-R", str(tmp_path)])
    os.chdir(tmp_path / "sub" / "two(1.0)" / "gene_models")

    res = _find_resource(repo_fixture.proto, str(tmp_path))
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_find_resource_without_version(repo_fixture, tmp_path):

    cli_manage(["repo-manifest", "-R", str(tmp_path)])
    os.chdir(tmp_path / "one")

    res = _find_resource(repo_fixture.proto, str(tmp_path))
    assert res.resource_id == "one"
    assert res.version == (0,)


def test_find_resource_with_resource_id(repo_fixture, tmp_path):

    res = _find_resource(
        repo_fixture.proto, str(tmp_path), resource="sub/two")
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_repo_init(tmp_path):
    # When
    cli_manage(["repo-init", "-R", str(tmp_path)])

    # Then
    assert (tmp_path / ".CONTENTS").exists()


def test_repo_init_inside_repo(tmp_path):
    # Given
    (tmp_path / "inside").mkdir()
    cli_manage(["repo-init", "-R", str(tmp_path)])

    # When
    with pytest.raises(SystemExit, match="1"):
        cli_manage(["repo-init", "-R", str(tmp_path / "inside")])

    # Then
    assert not (tmp_path / "inside" / ".CONTENTS").exists()
