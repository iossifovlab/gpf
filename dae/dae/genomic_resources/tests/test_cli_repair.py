# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import textwrap

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GR_CONTENTS_FILE_NAME,
    GR_MANIFEST_FILE_NAME,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_protocol,
    setup_directories,
    setup_tabix,
)


@pytest.fixture()
def proto_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, FsspecReadWriteProtocol]:
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
        },
        "two": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                    filename: data.txt.gz
                    format: tabix
                    zero_based: true
                scores:
                    - id: phastCons100way
                      type: float
                      name: s1
                histograms:
                    - score: phastCons100way
                      bins: 100
                """),
        },
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
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        2       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2)
    proto = build_filesystem_test_protocol(path)
    return path, proto


def test_resource_repair_simple(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
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


def test_repo_repair_simple(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/statistics").exists()
    assert not (path / "two/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    cli_manage([
        "repo-repair", "-R", str(path), "-j", "1"])

    # Then
    assert (path / "one/statistics").exists()
    assert (path / "one" / GR_MANIFEST_FILE_NAME).exists()
    assert (path / "two/statistics").exists()
    assert (path / "two" / GR_MANIFEST_FILE_NAME).exists()
    assert (path / GR_CONTENTS_FILE_NAME).exists()


def test_resource_repair_dry_run(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))

    proto.filesystem.delete(str(path / "one" / ".MANIFEST"))

    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    with pytest.raises(SystemExit):
        cli_manage([
            "resource-repair", "--dry-run",
            "-R", str(path), "-r", "one",
            "-j", "1"])

    # Then
    assert not (path / "one/statistics").exists()
    assert not (path / "one/.MANIFEST").exists()


def test_repo_repair_dry_run(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    # Given
    path, proto = proto_fixture
    proto.filesystem.delete(
        os.path.join(proto.url, ".CONTENTS"))
    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()

    # When
    with pytest.raises(SystemExit):
        cli_manage([
            "repo-repair", "--dry-run", "-R", str(path), "-j", "1"])

    # Then
    assert not (path / "one/statistics").exists()
    assert not (path / GR_CONTENTS_FILE_NAME).exists()
