# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.draw_resource_histogram import main
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
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
    path = tmp_path_factory.mktemp("draw_histogram_proto_fixture")
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


def test_draw_resource_histogram(
    proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    path, proto = proto_fixture

    assert not (path / "one/statistics/histogram_phastCons100way.png").exists()
    cli_manage([
        "resource-repair", "-R", str(path), "-r", "one", "-j", "1"])
    assert (path / "one/statistics/histogram_phastCons100way.png").exists()

    proto.filesystem.delete(
      path / "one/statistics/histogram_phastCons100way.png"
    )
    assert not (path / "one/statistics/histogram_phastCons100way.png").exists()

    main([
        "-R", str(path),
        "-r", "one",
    ])
    assert (path / "one/statistics/histogram_phastCons100way.png").exists()
