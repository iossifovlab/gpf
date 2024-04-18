# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import box
from sqlalchemy import inspect

from dae.gene_profile.db import GeneProfileDB
from dae.gene_profile.statistic import GPStatistic
from dae.gpf_instance import GPFInstance


def test_gpdb_table_building(
    tmp_path: pathlib.Path,
    gp_config: box.Box,
) -> None:
    gpdb_filename = str(tmp_path / "gpdb")
    gpdb = GeneProfileDB(
        gp_config,
        gpdb_filename,
    )
    inspector = inspect(gpdb.engine)

    cols = []
    for column in inspector.get_columns("gene_profile"):
        cols.append(column["name"])
    print(cols)

    assert set(cols).difference(
        set([
            "symbol_name",
            "relevant_gene_sets_rank",
            "main_FMRP Darnell",
            "main_CHD8 target genes",
            "autism_scores_RVIS",
            "autism_scores_RVIS_rank",
            "autism_scores_SFARI gene score",
            "protection_scores_RVIS",
            "protection_scores_RVIS_rank",
            "protection_scores_SFARI gene score",
            "iossifov_2014_unaffected_denovo_missense_rate",
            "iossifov_2014_unaffected_denovo_missense",
            "iossifov_2014_unaffected_denovo_noncoding_rate",
            "iossifov_2014_unaffected_denovo_noncoding",
            "iossifov_2014_autism_denovo_missense_rate",
            "iossifov_2014_autism_denovo_missense",
            "iossifov_2014_autism_denovo_noncoding_rate",
            "iossifov_2014_autism_denovo_noncoding",
        ]),
    ) == set()


def test_gpdb_insert_and_get_gp(
        tmp_path: pathlib.Path,
        gp_gpf_instance: GPFInstance,
        sample_gp: GPStatistic,
        gp_config: box.Box) -> None:

    gpdb_filename = str(tmp_path / "gpdb")
    gpdb = GeneProfileDB(
        gp_config, gpdb_filename, clear=True)
    gpdb.insert_gp(sample_gp)
    gp = gpdb.get_gp("CHD8")

    assert gp is not None

    assert gp.gene_sets == [
        "main_CHD8 target genes",
    ]

    assert gp.genomic_scores["autism_scores"] == {
        "SFARI gene score": {"value": 1.0, "format": "%s"},
        "RVIS_rank": {"value": 193.0, "format": "%s"},
        "RVIS": {"value": -2.34, "format": "%s"},
    }

    assert gp.genomic_scores["protection_scores"] == {
        "SFARI gene score": {"value": 1.0, "format": "%s"},
        "RVIS_rank": {"value": 193.0, "format": "%s"},
        "RVIS": {"value": -2.34, "format": "%s"},
    }

    assert gp.variant_counts == {
        "iossifov_2014": {
            "autism": {
                "denovo_noncoding": {"count": 0, "rate": 0},
                "denovo_missense": {"count": 0, "rate": 0},
            },
            "unaffected": {
                "denovo_noncoding": {"count": 0, "rate": 0},
                "denovo_missense": {"count": 0, "rate": 0},
            },
        },
    }


def test_gpdb_sort(
        gp_gpf_instance: GPFInstance,
        sample_gp: GPStatistic) -> None:
    sample_gp.gene_symbol = "CHD7"
    sample_scores = sample_gp.genomic_scores
    sample_scores["protection_scores"]["SFARI gene score"] = -11
    gp_gpf_instance._gene_profile_db.insert_gp(sample_gp)
    stats_unsorted = gp_gpf_instance.query_gp_statistics(1)
    stats_sorted = gp_gpf_instance.query_gp_statistics(
        1, sort_by="protection_scores_SFARI gene score", order="asc",
    )
    assert stats_unsorted[0]["geneSymbol"] == "CHD8"
    assert stats_unsorted[1]["geneSymbol"] == "CHD7"

    assert stats_sorted[0]["geneSymbol"] == "CHD7"
    assert stats_sorted[1]["geneSymbol"] == "CHD8"

    stats_sorted = gp_gpf_instance.query_gp_statistics(
        1, sort_by="autism_scores_SFARI gene score", order="desc",
    )
    stats_sorted = gp_gpf_instance.query_gp_statistics(
        1,
        sort_by="iossifov_2014_autism_denovo_noncoding", order="desc",
    )
    stats_sorted = gp_gpf_instance.query_gp_statistics(
        1, sort_by="main_CHD8 target genes", order="desc",
    )
