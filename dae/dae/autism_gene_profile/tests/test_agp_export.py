# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from box import Box

import pytest
from pytest_mock import MockerFixture

from dae.autism_gene_profile.exporter import cli_export
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.autism_gene_profile.statistic import AGPStatistic

from dae.gpf_instance import GPFInstance


@pytest.fixture
def two_rows_agp(
    agp_config: Box, sample_agp: AGPStatistic,
    agp_gpf_instance: GPFInstance,
    mocker: MockerFixture,
    tmp_path: pathlib.Path
) -> GPFInstance:
    root_path = tmp_path
    agpdb_filename = str(root_path / "agpdb")
    agpdb = AutismGeneProfileDB(agp_config, agpdb_filename, clear=True)
    agpdb.insert_agp(sample_agp)

    sample_agp.gene_symbol = "CHD7"
    sample_scores = sample_agp.genomic_scores
    sample_scores["protection_scores"]["SFARI_gene_score"] = -11
    agpdb.insert_agp(sample_agp)

    mocker.patch.object(
        agp_gpf_instance,
        "_autism_gene_profile_db",
        agpdb)

    return agp_gpf_instance


def test_agp_export_no_output(
        two_rows_agp: GPFInstance,
        capsys: pytest.CaptureFixture) -> None:

    cli_export([], two_rows_agp)
    out, _err = capsys.readouterr()

    lines = list(filter(len, out.split("\n")))
    assert len(lines) == 3


def test_agp_export(
        two_rows_agp: GPFInstance,
        tmp_path: pathlib.Path) -> None:

    outfile = str(tmp_path / "agp_export.tsv")
    cli_export(["-o", outfile], two_rows_agp)

    assert (tmp_path / "agp_export.tsv").exists()
    content = (tmp_path / "agp_export.tsv").read_text()
    lines = list(filter(len, content.split("\n")))
    assert len(lines) == 3
