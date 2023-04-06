# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.testing import build_filesystem_test_protocol, \
    setup_directories
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME


@pytest.fixture
def proto_fixture(content_fixture, tmp_path_factory):
    path = tmp_path_factory.mktemp("cli_manifest_proto_fixture")
    setup_directories(
        path,
        content_fixture)
    proto = build_filesystem_test_protocol(path)
    return path, proto


def test_resource_manifest_simple(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))

    assert not (path / GR_CONTENTS_FILE_NAME).exists()
    assert not (path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "resource-manifest", "-R", str(path), "-r", "one"])

    # Then
    assert (path / "one/.MANIFEST").is_file()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_manifest_dry_run_simple(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))

    assert not (path / GR_CONTENTS_FILE_NAME).exists()
    assert not (path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "resource-manifest", "-R", str(path), "-r", "one", "--dry-run"])

    # Then
    assert not (path / "one/.MANIFEST").exists()


def test_repo_manifest_simple(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))

    assert not (path / GR_CONTENTS_FILE_NAME).exists()
    assert not (path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "repo-manifest", "-R", str(path)])

    # Then
    assert (path / "one/.MANIFEST").is_file()
    assert (path / GR_CONTENTS_FILE_NAME).exists()


def test_repo_manifest_dry_run_simple(proto_fixture):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))

    assert not (path / GR_CONTENTS_FILE_NAME).exists()
    assert not (path / "one/.MANIFEST").exists()

    # When
    cli_manage([
        "repo-manifest", "-R", str(path), "--dry-run"])

    # Then
    assert not (path / "one/.MANIFEST").exists()


def test_repo_manifest_no_agruments(
        proto_fixture, mocker, capsys, caplog):
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))
    cli_manage([
        "-VV", "repo-manifest", "-R", str(path)])
    mocker.patch("os.getcwd", return_value=str(path))
    capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage(["repo-manifest"])

    # Then
    out, err = capsys.readouterr()

    assert err == ""
    assert out == \
        f"working with repository: {path}\n"
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
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


def test_check_manifest_update(proto_fixture):
    # Given
    _path, proto = proto_fixture
    res = proto.get_resource("one")

    # When
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # Then
    manifest_update = proto.check_update_manifest(res)
    assert bool(manifest_update)


def test_resource_run_manifest_update(proto_fixture):
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto.check_update_manifest(res))

    # When
    cli_manage([
        "resource-manifest", "-R", str(path), "-r", "one"])

    # Then
    assert not bool(proto.check_update_manifest(res))


def test_repo_run_manifest_update(proto_fixture):
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto.check_update_manifest(res))

    # When
    cli_manage([
        "repo-manifest", "-R", str(path)])

    # Then
    assert not bool(proto.check_update_manifest(res))


def test_resource_dry_run_manifest_update(proto_fixture):
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto.check_update_manifest(res))

    # When
    cli_manage([
        "resource-manifest", "--dry-run", "-R", str(path), "-r", "one"])

    # Then
    assert bool(proto.check_update_manifest(res))


def test_repo_dry_run_manifest_update(proto_fixture):
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto.check_update_manifest(res))

    # When
    cli_manage([
        "repo-manifest", "--dry-run", "-R", str(path)])

    # Then
    assert bool(proto.check_update_manifest(res))


def test_resource_dry_run_manifest_needs_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-manifest", "--dry-run",
            "-R", str(path), "-r", "one"])

    # Then
    assert bool(proto.check_update_manifest(res))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO,
         "manifest of <one> should be updated; entries to update in manifest "
         "['data.txt']"),
    ]


def test_repo_dry_run_manifest_needs_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-manifest", "--dry-run", "-R", str(path)])

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
         "manifest of <sub/two> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <sub/two(1.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <three(2.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <xxxxx-genome> is up to date"),
    ]


def test_resource_dry_run_manifest_no_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "resource-manifest", "--dry-run",
            "-R", str(path), "-r", "one"])

    # Then
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO, "manifest of <one> is up to date")
    ]


def test_resource_manifest_no_agruments(
        proto_fixture, mocker, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    cli_manage([
        "repo-manifest", "-R", str(path)])

    mocker.patch("os.getcwd", return_value=str(path / "one"))
    capsys.readouterr()

    # When
    with caplog.at_level(logging.INFO):
        cli_manage(["resource-manifest"])

    # Then
    out, err = capsys.readouterr()

    assert err == ""
    assert out == f"working with repository: {path}\n"
    assert caplog.record_tuples == [
        ("dae.genomic_resources.repository_factory", logging.INFO,
         "using default GRR definitions"),
        ("grr_manage", logging.INFO, "manifest of <one> is up to date")
    ]


def test_repo_dry_run_manifest_no_update_message(
        proto_fixture, capsys, caplog):
    # Given
    path, _proto = proto_fixture
    # When
    with caplog.at_level(logging.INFO):
        cli_manage([
            "repo-manifest", "--dry-run", "-R", str(path)])

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
         "manifest of <sub/two> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <sub/two(1.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <three(2.0)> is up to date"),
        ("grr_manage", logging.INFO,
         "manifest of <xxxxx-genome> is up to date"),
    ]
