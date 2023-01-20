# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_filesystem_test_protocol, \
    setup_directories, setup_tabix


@pytest.fixture
def proto_fixture(tmp_path_factory):
    path = tmp_path_factory.mktemp("cli_info_repo_fixture")
    setup_directories(
        path,
        {
            "one": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: position_score
                    table:
                        filename: data.txt.gz
                        format: tabix
                    scores:
                        - id: phastCons100way
                          type: float
                          name: s1
                    histograms:
                        - score: phastCons100way
                          bins: 100
                    """),
            },
            "two": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: allele_score
                    table:
                        filename: data.txt.gz
                        format: tabix
                        reference:
                            name: REF
                        alternative:
                            name: ALT
                    scores:
                        - id: AC
                          type: int
                          name: AC
                    """),
            }
        })
    setup_tabix(
        path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        2       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2)
    setup_tabix(
        path / "two" / "data.txt.gz",
        """
        #chrom  pos_begin    chrom  variant    REF  ALT  AC
        1       12198        1      sub(G->C)  G    C    0
        1       12237        1      sub(G->A)  G    A    0
        1       12259        1      sub(G->C)  G    C    0
        1       12266        1      sub(G->A)  G    A    0
        1       12272        1      sub(G->A)  G    A    0
        1       12554        1      sub(A->G)  A    G    0
        """, seq_col=0, start_col=1, end_col=1)
    proto = build_filesystem_test_protocol(path)
    return path, proto


def test_resource_info(proto_fixture):
    path, _proto = proto_fixture
    assert not (path / "one/index.html").exists()

    cli_manage(["resource-info", "-R", str(path), "-r", "one"])

    assert (path / "one/index.html").exists()
    assert not (path / "two/index.html").exists()
    assert not (path / "index.html").exists()

    cli_manage(["resource-info", "-R", str(path), "-r", "two"])

    assert (path / "one/index.html").exists()
    assert (path / "two/index.html").exists()
    assert not (path / "index.html").exists()

    with open(path / "one/index.html") as infile:
        result = infile.read()

    assert result.find("<h1>one</h1>")
    assert result.find("<h3>Score file:</h3>")
    assert result.find("<h3>Score definitions:</h3>")
    assert result.find("<p>Score ID: phastCons100way</p>")
    assert result.find("<h3>Histograms:</h3>")
    print(result)


def test_repo_info(proto_fixture):
    path, _proto = proto_fixture

    assert not (path / "one/index.html").exists()

    cli_manage(["repo-info", "-R", str(path)])

    assert (path / "one/index.html").exists()
    assert (path / "two/index.html").exists()
    assert (path / "index.html").exists()
