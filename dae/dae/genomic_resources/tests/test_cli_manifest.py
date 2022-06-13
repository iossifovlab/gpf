# pylint: disable=W0621,C0114,C0116,W0212,W0613

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


def test_cli_manifest_simple(proto_fixture, tmp_path):

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).is_file()
    assert (tmp_path / "one/.MANIFEST").is_file()
    cli_manage(["manifest", str(tmp_path), "one"])
    assert (tmp_path / "one/.MANIFEST").is_file()


def test_cli_check_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")

    # When
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # Then
    manifest_update = proto_fixture.check_update_manifest(res)
    assert bool(manifest_update)


def test_cli_run_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    cli_manage(["manifest", str(tmp_path), "one"])

    # Then
    assert not bool(proto_fixture.check_update_manifest(res))


def test_cli_dry_run_manifest_update(proto_fixture, tmp_path):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    cli_manage(["manifest", "--dry-run", str(tmp_path), "one"])

    # Then
    assert bool(proto_fixture.check_update_manifest(res))


def test_cli_dry_run_manifest_needs_update_message(
        proto_fixture, tmp_path, capsys):
    # Given
    res = proto_fixture.get_resource("one")
    with res.open_raw_file("data.txt", "wt") as outfile:
        outfile.write("alabala2")

    # When
    cli_manage(["manifest", "--dry-run", str(tmp_path), "one"])

    # Then
    captured = capsys.readouterr()
    print(captured.err)
    assert captured.err == \
        "manifest of <one> should be updated; " \
        "entries to delete from manifest set(); " \
        "entries to update in manifest {'data.txt'};\n"


def test_cli_dry_run_manifest_no_update_message(
        proto_fixture, tmp_path, capsys):
    # Given

    # When
    cli_manage(["manifest", "--dry-run", str(tmp_path), "one"])

    # Then
    captured = capsys.readouterr()
    print(captured.err)
    assert captured.err == \
        "manifest of <one> is up to date\n"
