# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_testing_protocol, \
    tabix_to_resource


@pytest.fixture
def proto_fixture(tmp_path, tabix_file):
    proto = build_testing_protocol(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: position_score
                    table:
                        filename: data.bgz
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
                        filename: data.bgz
                        format: tabix
                        scores:
                            - id: AC
                              type: int
                              name: AC
                        reference:
                            name: REF
                        alternative:
                            name: ALT
                    """),
            }
        })
    resource = proto.get_resource("one")
    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end  s1    s2
            1       10         15       0.02  1.02
            1       17         19       0.03  1.03
            1       22         25       0.04  1.04
            2       5          80       0.01  2.01
            2       10         11       0.02  2.02
            """, seq_col=0, start_col=1, end_col=2),
        resource, "data.bgz"
    )
    resource = proto.get_resource("two")
    tabix_to_resource(
        tabix_file(
            """
            #CHROM  POS    chrom  variant    REF  ALT  AC
            1       12198  1      sub(G->C)  G    C    0
            1       12237  1      sub(G->A)  G    A    0
            1       12259  1      sub(G->C)  G    C    0
            1       12266  1      sub(G->A)  G    A    0
            1       12272  1      sub(G->A)  G    A    0
            1       12554  1      sub(A->G)  A    G    0
            """, seq_col=0, start_col=1, end_col=1),
        resource, "data.bgz"
    )
    return proto


def test_resource_info(proto_fixture, dask_mocker, tmp_path):
    assert not (tmp_path / "one/index.html").exists()

    cli_manage(["resource-info", "-R", str(tmp_path), "-r", "one"])

    assert (tmp_path / "one/index.html").exists()
    assert not (tmp_path / "two/index.html").exists()
    assert not (tmp_path / "index.html").exists()

    cli_manage(["resource-info", "-R", str(tmp_path), "-r", "two"])

    assert (tmp_path / "one/index.html").exists()
    assert (tmp_path / "two/index.html").exists()
    assert not (tmp_path / "index.html").exists()

    with open(tmp_path / "one/index.html") as infile:
        result = infile.read()

    assert result.find("<h1>one</h1>")
    assert result.find("<h3>Score file:</h3>")
    assert result.find("<h3>Score definitions:</h3>")
    assert result.find("<p>Score ID: phastCons100way</p>")
    assert result.find("<h3>Histograms:</h3>")
    print(result)


def test_repo_info(proto_fixture, dask_mocker, tmp_path):
    assert not (tmp_path / "one/index.html").exists()

    cli_manage(["repo-info", "-R", str(tmp_path)])

    assert (tmp_path / "one/index.html").exists()
    assert (tmp_path / "two/index.html").exists()
    assert (tmp_path / "index.html").exists()
