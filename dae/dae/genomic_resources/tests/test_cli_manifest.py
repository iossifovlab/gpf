# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.testing import build_testing_protocol
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME


@pytest.fixture
def proto_fixture(content_fixture, tmp_path):
    return build_testing_protocol(
        scheme="file",
        root_path=str(tmp_path),
        content=content_fixture)


def test_resource_manifest_simple(proto_fixture, tmp_path):
    # Given
    proto_fixture.filesystem.delete(str(tmp_path / "one/.MANIFEST"))

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()
    assert not (tmp_path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "resource-manifest", "-R", str(tmp_path), "-r", "one"])

    # Then
    assert (tmp_path / "one/.MANIFEST").is_file()
    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_manifest_dry_run_simple(proto_fixture, tmp_path):
    # Given
    proto_fixture.filesystem.delete(str(tmp_path / "one/.MANIFEST"))

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()
    assert not (tmp_path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "resource-manifest", "-R", str(tmp_path), "-r", "one", "--dry-run"])

    # Then
    assert not (tmp_path / "one/.MANIFEST").exists()


def test_repo_manifest_simple(proto_fixture, tmp_path):
    # Given
    proto_fixture.filesystem.delete(str(tmp_path / "one/.MANIFEST"))

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()
    assert not (tmp_path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "repo-manifest", "-R", str(tmp_path)])

    # Then
    assert (tmp_path / "one/.MANIFEST").is_file()
    assert (tmp_path / GR_CONTENTS_FILE_NAME).exists()


def test_repo_manifest_dry_run_simple(proto_fixture, tmp_path):
    # Given
    proto_fixture.filesystem.delete(str(tmp_path / "one/.MANIFEST"))

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).exists()
    assert not (tmp_path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "repo-manifest", "-R", str(tmp_path), "--dry-run"])

    # Then
    assert not (tmp_path / "one/.MANIFEST").exists()


def test_repo_manifest_no_agruments(
        proto_fixture, tmp_path, mocker, capsys, caplog):
    # Given
    cli_manage([
        "-VV", "repo-manifest", "-R", str(tmp_path)])
    mocker.patch("os.getcwd", return_value=str(tmp_path))
    capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage(["repo-manifest"])

    # Then
    out, err = capsys.readouterr()

    assert out == ""
    assert err == \
        f"working with repository: {tmp_path}\n"
    assert caplog.record_tuples == [
        ("grr_manage",
         logging.INFO,
         "manifest of <one> is up to date"),
        ("grr_manage",
         logging.INFO,
         "manifest of <sub/two> is up to date"),
        ("grr_manage",
         logging.INFO,
         "manifest of <sub/two(1.0)> is up to date"),
        ("grr_manage",
         logging.INFO,
         "manifest of <three(2.0)> is up to date"),
        ("grr_manage",
         logging.INFO,
         "manifest of <xxxxx-genome> is up to date"),
    ]


def test_check_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")

    # When
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # Then
    manifest_update = proto_fixture.check_update_manifest(res)
    assert bool(manifest_update)


def test_resource_run_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto_fixture.check_update_manifest(res))

    # When
    cli_manage([
        "resource-manifest", "-R", str(tmp_path), "-r", "one"])

    # Then
    assert not bool(proto_fixture.check_update_manifest(res))


def test_repo_run_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto_fixture.check_update_manifest(res))

    # When
    cli_manage([
        "repo-manifest", "-R", str(tmp_path)])

    # Then
    assert not bool(proto_fixture.check_update_manifest(res))


def test_resource_dry_run_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto_fixture.check_update_manifest(res))

    # When
    cli_manage([
        "resource-manifest", "--dry-run", "-R", str(tmp_path), "-r", "one"])

    # Then
    assert bool(proto_fixture.check_update_manifest(res))


def test_repo_dry_run_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto_fixture.check_update_manifest(res))

    # When
    cli_manage([
        "repo-manifest", "--dry-run", "-R", str(tmp_path)])

    # Then
    assert bool(proto_fixture.check_update_manifest(res))


def test_resource_dry_run_manifest_needs_update_message(
        proto_fixture, tmp_path, capsys, caplog):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-manifest", "--dry-run",
            "-R", str(tmp_path), "-r", "one"])

    # Then
    assert bool(proto_fixture.check_update_manifest(res))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == [
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
    ]


def test_repo_dry_run_manifest_needs_update_message(
        proto_fixture, tmp_path, capsys, caplog):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-manifest", "--dry-run", "-R", str(tmp_path)])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == [
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
        ("grr_manage", logging.INFO,
         "manifest of <sub/two> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <sub/two(1.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <three(2.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <xxxxx-genome> is up to date"),
    ]


def test_resource_dry_run_manifest_no_update_message(
        proto_fixture, tmp_path, capsys, caplog):
    # Given

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-manifest", "--dry-run",
            "-R", str(tmp_path), "-r", "one"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == [
        ("grr_manage", logging.INFO, "manifest of <one> is up to date")
    ]


def test_resource_manifest_no_agruments(
        proto_fixture, tmp_path, mocker, capsys, caplog):
    # Given
    cli_manage([
        "repo-manifest", "-R", str(tmp_path)])

    mocker.patch("os.getcwd", return_value=str(tmp_path / "one"))
    capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage(["resource-manifest"])

    # Then
    out, err = capsys.readouterr()

    assert out == ""
    assert err == f"working with repository: {tmp_path}\n"
    assert caplog.record_tuples == [
        ("grr_manage", logging.INFO, "manifest of <one> is up to date")
    ]


def test_repo_dry_run_manifest_no_update_message(
        proto_fixture, tmp_path, capsys, caplog):
    # Given

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-manifest", "--dry-run", "-R", str(tmp_path)])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert caplog.record_tuples == [
        ("grr_manage", logging.INFO,
         "manifest of <one> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <sub/two> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <sub/two(1.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <three(2.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <xxxxx-genome> is up to date"),
    ]
