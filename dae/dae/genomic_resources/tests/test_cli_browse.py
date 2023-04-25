# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap

import pytest
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.cli import cli_browse
from dae.genomic_resources.testing import build_filesystem_test_repository, \
    setup_directories


@pytest.fixture
def repo_fixture(tmp_path_factory):
    path = tmp_path_factory.mktemp("cli_browse_repo_fixture")
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


@pytest.fixture
def repo_def(tmp_path_factory, repo_fixture):
    path, _repo = repo_fixture
    root_path = tmp_path_factory.mktemp("repo_def")
    setup_directories(root_path, {
        ".grr_definition.yaml": textwrap.dedent(f"""
        id: "test_grr"
        type: "directory"
        directory: "{str(path)}"
        """)
    })

    return root_path / ".grr_definition.yaml"


def test_cli_browse_with_grr_argument(repo_fixture, repo_def, capsys):

    cli_browse(["--grr", str(repo_def)])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Working with GRR definition: " + str(repo_def) + "\n" \
        "{'directory': '" + str(repo_fixture[0]) + "',\n" \
        " 'id': 'test_grr',\n" \
        " 'type': 'directory'}\n" \
        "Basic                0        2 7.0 B        test_grr one\n" \
        "gene_models          1.0      2 50.0 B       test_grr sub/two\n"


def test_cli_browse_with_env_variable(repo_fixture, repo_def, capsys, mocker):

    mocker.patch.dict(
        os.environ, {"GRR_DEFINITION_FILE": str(repo_def)})

    cli_browse([])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Working with GRR definition: " + str(repo_def) + "\n" \
        "{'directory': '" + str(repo_fixture[0]) + "',\n" \
        " 'id': 'test_grr',\n" \
        " 'type': 'directory'}\n" \
        "Basic                0        2 7.0 B        test_grr one\n" \
        "gene_models          1.0      2 50.0 B       test_grr sub/two\n"


def test_cli_browse_default_defintion(repo_fixture, repo_def, capsys, mocker):

    mocker.patch.dict(os.environ, {"HOME": str(repo_def.parent)})
    os.environ.pop("GRR_DEFINITION_FILE", None)

    cli_browse([])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Working with GRR definition: " + str(repo_def) + "\n" \
        "{'directory': '" + str(repo_fixture[0]) + "',\n" \
        " 'id': 'test_grr',\n" \
        " 'type': 'directory'}\n" \
        "Basic                0        2 7.0 B        test_grr one\n" \
        "gene_models          1.0      2 50.0 B       test_grr sub/two\n"
