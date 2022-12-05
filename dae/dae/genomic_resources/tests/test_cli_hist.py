# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import logging
import textwrap

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GR_CONTENTS_FILE_NAME
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
    return proto


def test_resource_histograms_simple(proto_fixture, dask_mocker, tmp_path):
    # Given
    proto_fixture.filesystem.delete(
        os.path.join(proto_fixture.url, ".CONTENTS"))
    assert not (tmp_path / "one/histograms").exists()
    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage(["resource-histograms", "-R", str(tmp_path), "-r", "one"])

    # Then
    assert (tmp_path / "one/histograms").exists()
    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()


def test_repo_histograms_simple(proto_fixture, dask_mocker, tmp_path):

    # Given
    proto_fixture.filesystem.delete(
        os.path.join(proto_fixture.url, ".CONTENTS"))
    assert not (tmp_path / "one/histograms").exists()
    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage(["repo-histograms", "-R", str(tmp_path)])

    # Then
    assert (tmp_path / "one/histograms").exists()
    assert (tmp_path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_histograms_dry_run(proto_fixture, dask_mocker, tmp_path):
    # Given
    assert not (tmp_path / "one/histograms").exists()

    # When
    cli_manage([
        "resource-histograms", "--dry-run", "-R", str(tmp_path), "-r", "one"])

    # Then
    assert not (tmp_path / "one/histograms").exists()


def test_repo_histograms_dry_run(proto_fixture, dask_mocker, tmp_path):
    # Given
    proto_fixture.filesystem.delete(
        os.path.join(proto_fixture.url, ".CONTENTS"))
    assert not (tmp_path / "one/histograms").exists()
    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "repo-histograms", "--dry-run", "-R", str(tmp_path)])

    # Then
    assert not (tmp_path / "one/histograms").exists()
    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_histograms_need_update_message(
        proto_fixture, dask_mocker, tmp_path, capsys, caplog):

    # Given
    assert not (tmp_path / "one/histograms").exists()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-histograms", "--dry-run",
            "-R", str(tmp_path), "-r", "one"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "resource <one> histograms "
         "[{'score': 'phastCons100way', 'bins': 100}] need update"),
    ]


def test_repo_histograms_need_update_message(
        proto_fixture, dask_mocker, tmp_path, capsys, caplog):

    # Given
    assert not (tmp_path / "one/histograms").exists()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-histograms", "--dry-run", "-R", str(tmp_path)])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "resource <one> histograms "
         "[{'score': 'phastCons100way', 'bins': 100}] need update"),
    ]


def test_resource_histograms_no_update_message(
        proto_fixture, dask_mocker, tmp_path, capsys, caplog):
    # Given
    assert not (tmp_path / "one/histograms").exists()
    cli_manage([
        "resource-histograms", "-R", str(tmp_path), "-r", "one"])
    assert (tmp_path / "one/histograms").exists()
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-histograms", "--dry-run",
            "-R", str(tmp_path), "-r", "one"])

    # Then
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.histogram", logging.INFO,
         "histograms of <one> are up to date")
    ]


def test_repo_histograms_no_update_message(
        proto_fixture, dask_mocker, tmp_path, capsys, caplog):
    # Given
    assert not (tmp_path / "one/histograms").exists()
    cli_manage([
        "repo-histograms", "-R", str(tmp_path)])
    assert (tmp_path / "one/histograms").exists()
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-histograms", "--dry-run", "-R", str(tmp_path)])

    # Then
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.histogram", logging.INFO,
         "histograms of <one> are up to date")
    ]
