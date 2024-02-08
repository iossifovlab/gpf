# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from box import Box

import pytest
from pytest_mock import MockerFixture

from dae.gene_profile.exporter import cli_export
from dae.gene_profile.db import GeneProfileDB
from dae.gene_profile.statistic import GPStatistic

from dae.gpf_instance import GPFInstance


@pytest.fixture
def two_rows_gp(
    gp_config: Box, sample_gp: GPStatistic,
    gp_gpf_instance: GPFInstance,
    mocker: MockerFixture,
    tmp_path: pathlib.Path
) -> GPFInstance:
    root_path = tmp_path
    gpdb_filename = str(root_path / "gpdb")
    gpdb = GeneProfileDB(gp_config, gpdb_filename, clear=True)
    gpdb.insert_gp(sample_gp)

    sample_gp.gene_symbol = "CHD7"
    sample_scores = sample_gp.genomic_scores
    sample_scores["protection_scores"]["SFARI gene score"] = -11
    gpdb.insert_gp(sample_gp)

    mocker.patch.object(
        gp_gpf_instance,
        "_gene_profile_db",
        gpdb)

    return gp_gpf_instance


def test_gp_export_no_output(
        two_rows_gp: GPFInstance,
        capsys: pytest.CaptureFixture) -> None:

    cli_export([], two_rows_gp)
    out, _err = capsys.readouterr()

    lines = list(filter(len, out.split("\n")))
    assert len(lines) == 3


def test_gp_export(
        two_rows_gp: GPFInstance,
        tmp_path: pathlib.Path) -> None:

    outfile = str(tmp_path / "gp_export.tsv")
    cli_export(["-o", outfile], two_rows_gp)

    assert (tmp_path / "gp_export.tsv").exists()
    content = (tmp_path / "gp_export.tsv").read_text()
    lines = list(filter(len, content.split("\n")))
    assert len(lines) == 3
