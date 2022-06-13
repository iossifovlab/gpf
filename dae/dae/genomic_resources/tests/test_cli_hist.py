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


def test_cli_histograms_simple(proto_fixture, tmp_path):

    assert not (tmp_path / "one/histograms").exists()
    cli_manage(["histogram", str(tmp_path), "one"])
    assert (tmp_path / "one/histograms").exists()


def test_cli_histograms_dry_run(proto_fixture, tmp_path):

    assert not (tmp_path / "one/histograms").exists()
    cli_manage(["histogram", "--dry-run", str(tmp_path), "one"])
    assert not (tmp_path / "one/histograms").exists()


def test_cli_histograms_need_update_message(proto_fixture, tmp_path, capsys):

    assert not (tmp_path / "one/histograms").exists()
    cli_manage(["histogram", "--dry-run", str(tmp_path), "one"])

    captured = capsys.readouterr()

    assert captured.err == \
        "resource <one> histograms " \
        "[{'score': 'phastCons100way', 'bins': 100}] need update\n"


def test_cli_histograms_no_update_message(proto_fixture, tmp_path, capsys):
    # Given
    assert not (tmp_path / "one/histograms").exists()
    cli_manage(["histogram", str(tmp_path), "one"])
    assert (tmp_path / "one/histograms").exists()
    _, _ = capsys.readouterr()

    # When
    cli_manage(["histogram", "--dry-run", str(tmp_path), "one"])

    # Then
    _, err = capsys.readouterr()
    assert err == \
        "resource <one> histograms are up to date\n"
