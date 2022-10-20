# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.autism_gene_profile.exporter import cli_export
from dae.autism_gene_profile.db import AutismGeneProfileDB


@pytest.fixture
def two_rows_agp(
        temp_dbfile, agp_config, sample_agp, agp_gpf_instance, mocker):
    agpdb = AutismGeneProfileDB(agp_config, temp_dbfile, clear=True)
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


def test_agp_export_no_output(two_rows_agp, capsys):

    cli_export([], two_rows_agp)
    out, _err = capsys.readouterr()

    lines = list(filter(len, out.split("\n")))
    assert len(lines) == 3


def test_agp_export(two_rows_agp, tmp_path):

    outfile = str(tmp_path / "agp_export.tsv")
    cli_export(["-o", outfile], two_rows_agp)

    assert (tmp_path / "agp_export.tsv").exists()
    content = (tmp_path / "agp_export.tsv").read_text()
    lines = list(filter(len, content.split("\n")))
    assert len(lines) == 3
