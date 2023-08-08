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


def test_resource_repair_simple(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one", "-j", "1"])

    # Then
    assert (path / "one/statistics").exists()
    assert (path / "one" / GR_MANIFEST_FILE_NAME).exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()


def test_repo_repair_simple(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "repo-repair", "-R", str(path), "-j", "1"])

    # Then
    assert (path / "one/statistics").exists()
    assert (path / "one" / GR_MANIFEST_FILE_NAME).exists()
    assert (path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_repair_dry_run(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))

    proto.filesystem.delete(str(path / "one" / ".MANIFEST"))

    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "resource-repair", "--dry-run",
        "-R", str(path), "-r", "one",
        "-j", "1"])

    # Then
    assert not (path / "one/statistics").exists()
    assert not (path / "one/.MANIFEST").exists()


def test_repo_repair_dry_run(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

    # Then
    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()


# def test_resource_repair_need_update_message(
#         proto_fixture, capsys, caplog, mocker):
#     path, _proto = proto_fixture
#     assert not (path / "one/statistics").exists()
#     with caplog.at_level(logging.INFO):
#         cli_manage([
#             "resource-repair", "--dry-run",
#             "-R", str(path), "-r", "one", "-j", "1"])

#     captured = capsys.readouterr()
#     assert captured.out == ""
#     assert captured.err == ""
#     assert caplog.record_tuples == [
#         ("dae.genomic_resources.repository_factory", logging.INFO,
#          "using default GRR definitions"),
#         ("grr_manage", logging.INFO,
#          "manifest of <one> is up to date"),
#         ("grr_manage", logging.INFO,
#          "No hash stored for <one>, need update"),
#         ("grr_manage", logging.INFO,
#          "Statistics of <one> need update"),
#         ("dae.genomic_resources.genomic_scores",
#          logging.WARNING,
#          "unable to load value range file: "
#          "statistics/min_max_phastCons100way.yaml"),
#         # ("dae.genomic_resources.genomic_scores",
#         #  logging.WARNING,
#         #  "unable to load histogram file: "
#         #  "statistics/histogram_phastCons100way.yaml"),
#     ]


# def test_repo_repair_need_update_message(
#         proto_fixture, capsys, caplog):
#     path, proto_fixture = proto_fixture
#     assert not (path / "one/statistics").exists()
#     with caplog.at_level(logging.INFO):
#         cli_manage([
#             "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

#     captured = capsys.readouterr()
#     assert captured.out == ""
#     assert captured.err == ""
#     assert caplog.record_tuples == [
#         ("dae.genomic_resources.repository_factory", logging.INFO,
#          "using default GRR definitions"),
#         ("grr_manage",
#          logging.INFO,
#          "manifest of <one> is up to date"),
#         ("grr_manage",
#          logging.INFO,
#          "No hash stored for <one>, need update"),
#         ("grr_manage",
#          logging.INFO,
#          "Statistics of <one> need update"),
#         ("dae.genomic_resources.genomic_scores",
#          logging.WARNING,
#          "unable to load value range file: "
#          "statistics/min_max_phastCons100way.yaml"),
#         # ("dae.genomic_resources.genomic_scores",
#         #  logging.WARNING,
#         #  "unable to load histogram file: "
#         #  "statistics/histogram_phastCons100way.yaml"),

#     ]


def test_resource_repair_no_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one", "-j", "1"])
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one", "-j", "1"])

    # Then
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> is up to date"),
        ("grr_manage", logging.INFO,
         "<one> statistics hash is up to date"),
    ]


def test_repo_repair_no_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "repo-repair", "-R", str(path), "-j", "1"])
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

    # Then
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> is up to date"),
        ("grr_manage", logging.INFO,
         "<one> statistics hash is up to date"),
    ]


def test_resource_repair_dry_run_needs_manifest_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, proto = proto_fixture
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one", "-j", "1"])

    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one",
            "-j", "1"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
        ("grr_manage", logging.INFO,
         "Manifest of <one> needs update, cannot check statistics"),
    ]


def test_repo_repair_dry_run_needs_manifest_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, proto = proto_fixture
    cli_manage([
        "repo-repair", "-R", str(path), "-j", "1"])
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
        ("grr_manage", logging.INFO,
         "Manifest of <one> needs update, cannot check statistics"),
    ]


def test_resource_repair_dry_run_needs_manifest_and_histogram_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one", "-j", "1"])

    setup_tabix(
        path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        3       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2, line_skip=1, force=True)
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one",
            "-j", "1"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt.gz', 'data.txt.gz.tbi']"),
        ("grr_manage", logging.INFO,
         "Manifest of <one> needs update, cannot check statistics"),
    ]

    # And after that::
    # Given
    cli_manage([
        "resource-manifest", "-R", str(path), "-r", "one", ])
    _, _ = capsys.readouterr()
    caplog.clear()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one",
            "-j", "1"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> is up to date"),
        ("grr_manage", logging.INFO,
         "Stored hash for <one> is outdated, need update"),
        ("grr_manage", logging.INFO,
         "Statistics of <one> need update"),
    ]


def test_repo_repair_dry_run_needs_manifest_and_histogram_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "repo-repair", "-R", str(path), "-j", "1"])

    setup_tabix(
        path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        3       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2, line_skip=1, force=True)
    _, _ = capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt.gz', 'data.txt.gz.tbi']"),
        ("grr_manage", logging.INFO,
         "Manifest of <one> needs update, cannot check statistics"),
    ]

    # And after that::
    # Given
    cli_manage([
        "repo-manifest", "-R", str(path), ])
    _, _ = capsys.readouterr()
    caplog.clear()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> is up to date"),
        ("grr_manage", logging.INFO,
         "Stored hash for <one> is outdated, need update"),
        ("grr_manage", logging.INFO,
         "Statistics of <one> need update"),
    ]
