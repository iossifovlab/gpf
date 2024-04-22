# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Any

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME
from dae.genomic_resources.testing import (
    build_filesystem_test_protocol,
    setup_directories,
)


@pytest.fixture()
def proto_fixture(
    content_fixture: dict[str, Any],
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, FsspecReadWriteProtocol]:
    path = tmp_path_factory.mktemp("cli_manifest_proto_fixture")
    setup_directories(
        path,
        content_fixture)
    proto = build_filesystem_test_protocol(path)
    return path, proto


def test_resource_manifest_simple(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
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


def test_resource_manifest_dry_run_simple(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))

    assert not (path / GR_CONTENTS_FILE_NAME).exists()
    assert not (path / "one/.MANIFEST").exists()

    # When
    with pytest.raises(SystemExit):
        cli_manage([
            "resource-manifest", "-R", str(path), "-r", "one", "--dry-run"])

    # Then
    assert not (path / "one/.MANIFEST").exists()


def test_repo_manifest_simple(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:

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


def test_repo_manifest_dry_run_simple(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(str(path / ".CONTENTS"))
    proto.filesystem.delete(str(path / "one/.MANIFEST"))

    assert not (path / GR_CONTENTS_FILE_NAME).exists()
    assert not (path / "one/.MANIFEST").exists()

    # When
    with pytest.raises(SystemExit):
        cli_manage([
            "repo-manifest", "-R", str(path), "--dry-run"])

    # Then
    assert not (path / "one/.MANIFEST").exists()


def test_check_manifest_update(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:

    # Given
    _path, proto = proto_fixture
    res = proto.get_resource("one")

    # When
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # Then
    manifest_update = proto.check_update_manifest(res)
    assert bool(manifest_update)


def test_resource_run_manifest_update(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:

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


def test_repo_run_manifest_update(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
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


def test_resource_dry_run_manifest_update(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:

    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto.check_update_manifest(res))

    # When
    with pytest.raises(SystemExit):
        cli_manage([
            "resource-manifest", "--dry-run", "-R", str(path), "-r", "one"])

    # Then
    assert bool(proto.check_update_manifest(res))


def test_repo_dry_run_manifest_update(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    # Given
    path, proto = proto_fixture
    res = proto.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")
    assert bool(proto.check_update_manifest(res))

    # When
    with pytest.raises(SystemExit):
        cli_manage([
            "repo-manifest", "--dry-run", "-R", str(path)])

    # Then
    assert bool(proto.check_update_manifest(res))
