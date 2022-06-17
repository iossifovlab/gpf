# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME
from dae.genomic_resources.cli import cli_manage
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
                    "genes.txt": demo_gtf_content
                }
            }
        })
    return repo


def test_cli_manifest(repo_fixture, tmp_path):

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).is_file()
    cli_manage(["manifest", str(tmp_path), "-r", "one"])
    assert (tmp_path / "one/.MANIFEST").is_file()


def test_cli_list(repo_fixture, tmp_path, capsys):

    cli_manage(["list", str(tmp_path)])
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        "Basic                0        2            7 one\n" \
        "gene_models          1.0      2           50 sub/two\n"
