# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap

import pytest
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.cli import cli_browse
from dae.genomic_resources.testing import build_testing_repository
from dae.testing import setup_directories


@pytest.fixture
def repo_fixture(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("test_repo")
    demo_gtf_content = "TP53\tchr3\t300\t200".encode("utf-8")
    repo = build_testing_repository(
        scheme="file",
        root_path=str(repo_path),
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
    repo.path = repo_path
    return repo


@pytest.fixture
def repo_def(tmp_path_factory, repo_fixture):
    root_path = tmp_path_factory.mktemp("repo_def")
    setup_directories(root_path, {
        ".grr_definition.yaml": textwrap.dedent(f"""
        id: "test_grr"
        type: "directory"
        directory: "{str(repo_fixture.path)}"
        """)
    })

    return root_path / ".grr_definition.yaml"


def test_cli_browse_with_grr_argument(repo_fixture, repo_def, capsys):

    cli_browse(["--grr", str(repo_def)])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Basic                0        2            7 one\n" \
        "gene_models          1.0      2           50 sub/two\n"


def test_cli_browse_with_env_variable(repo_fixture, repo_def, capsys, mocker):

    mocker.patch.dict(
        os.environ, {"GRR_DEFINITION_FILE": str(repo_def)})

    cli_browse([])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Basic                0        2            7 one\n" \
        "gene_models          1.0      2           50 sub/two\n"


def test_cli_browse_default_defintion(repo_fixture, repo_def, capsys, mocker):

    mocker.patch.dict(os.environ, {"HOME": str(repo_def.parent)})
    os.environ.pop("GRR_DEFINITION_FILE")

    cli_browse([])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Basic                0        2            7 one\n" \
        "gene_models          1.0      2           50 sub/two\n"