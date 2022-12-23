# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import logging
import textwrap

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GR_CONTENTS_FILE_NAME, \
    GR_MANIFEST_FILE_NAME
from dae.genomic_resources.testing import build_filesystem_test_protocol, \
    setup_directories, setup_tabix


@pytest.fixture
def proto_fixture(tmp_path_factory):
    path = tmp_path_factory.mktemp("cli_repair_proto_fixture")
    setup_directories(path, {
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
    proto = build_filesystem_test_protocol(path)
    return path, proto


def test_resource_repair_simple(proto_fixture, dask_mocker):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/histograms").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one"])

    # Then
    assert (path / "one/histograms").exists()
    assert (path / "one" / GR_MANIFEST_FILE_NAME).exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()


def test_repo_repair_simple(proto_fixture, dask_mocker):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/histograms").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "repo-repair", "-R", str(path)])

    # Then
    assert (path / "one/histograms").exists()
    assert (path / "one" / GR_MANIFEST_FILE_NAME).exists()
    assert (path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_repair_dry_run(proto_fixture, dask_mocker):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))

    proto.filesystem.delete(str(path / "one" / ".MANIFEST"))

    assert not (path / "one/histograms").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "resource-repair", "--dry-run", "-R", str(path), "-r", "one"])

    # Then
    assert not (path / "one/histograms").exists()
    assert not (path / "one/.MANIFEST").exists()


def test_repo_repair_dry_run(proto_fixture, dask_mocker):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/histograms").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "repo-repair", "--dry-run", "-R", str(path)])

    # Then
    assert not (path / "one/histograms").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_repair_need_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    path, _proto = proto_fixture
    assert not (path / "one/histograms").exists()
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "resource <one> histograms "
         "[{'score': 'phastCons100way', 'bins': 100}] need "
         "update"),
    ]


def test_repo_repair_need_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    path, proto_fixture = proto_fixture
    assert not (path / "one/histograms").exists()
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path)])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "resource <one> histograms "
         "[{'score': 'phastCons100way', 'bins': 100}] need update"),
    ]


def test_resource_repair_no_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one"])
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one"])

    # Then
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "histograms of <one> are up to date"),
    ]


def test_repo_repair_no_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "repo-repair", "-R", str(path)])
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path)])

    # Then
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "histograms of <one> are up to date"),
    ]


def test_resource_repair_dry_run_needs_manifest_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    # Given
    path, proto = proto_fixture
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one"])

    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run", "-R", str(path), "-r", "one"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
        ("grr_manage",
         logging.INFO,
         "manfiest one needs update; can't check histograms"),
    ]


def test_repo_repair_dry_run_needs_manifest_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    # Given
    path, proto = proto_fixture
    cli_manage([
        "repo-repair", "-R", str(path)])
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path)])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
        ("grr_manage",
         logging.INFO,
         "manfiest one needs update; can't check histograms"),
    ]


def test_resource_repair_dry_run_needs_manifest_and_histogram_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one"])

    setup_tabix(
        path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        2       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2, line_skip=1, force=True)
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run", "-R", str(path), "-r", "one"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt.gz', 'data.txt.gz.tbi']"),
        ("grr_manage",
         logging.INFO,
         "manfiest one needs update; can't check histograms"),
    ]

    # And after that::
    # Given
    cli_manage([
        "resource-manifest", "-R", str(path), "-r", "one"])
    _, _ = capsys.readouterr()
    caplog.clear()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run", "-R", str(path), "-r", "one"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "resource <one> histograms "
         "[{'score': 'phastCons100way', 'bins': 100}] need update"),
    ]


def test_repo_repair_dry_run_needs_manifest_and_histogram_update_message(
        proto_fixture, dask_mocker, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "repo-repair", "-R", str(path)])

    setup_tabix(
        path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        2       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2, line_skip=1, force=True)
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path)])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt.gz', 'data.txt.gz.tbi']"),
        ("grr_manage",
         logging.INFO,
         "manfiest one needs update; can't check histograms"),
    ]

    # And after that::
    # Given
    cli_manage([
        "repo-manifest", "-R", str(path)])
    _, _ = capsys.readouterr()
    caplog.clear()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path)])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("dae.genomic_resources.histogram",
         logging.INFO,
         "resource <one> histograms "
         "[{'score': 'phastCons100way', 'bins': 100}] need update"),
    ]
