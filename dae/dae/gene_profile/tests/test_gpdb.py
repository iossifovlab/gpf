# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import box
import duckdb
from pytest import approx

from dae.gene_profile.db import GeneProfileDBWriter
from dae.gene_profile.statistic import GPStatistic
from dae.gpf_instance import GPFInstance


def test_gpdb_table_building(
    tmp_path: pathlib.Path,
    gp_config: box.Box,
) -> None:
    gpdb_filename = str(tmp_path / "gpdb")
    gpdb = GeneProfileDBWriter(gp_config, gpdb_filename)

    cols = []
    with duckdb.connect(gpdb_filename, read_only=True) as connection:
        cols = [
            row["column_name"] for row in connection.execute(
                f"DESCRIBE {gpdb.table.alias_or_name}",
            ).df().to_dict("records")
        ]
    print(cols)

    assert set(cols).difference(
        [
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
        ],
    ) == set()


def test_gpdb_insert_and_get_gp(
        gp_gpf_instance: GPFInstance,
        gpdb_write: GeneProfileDBWriter,
        sample_gp: GPStatistic) -> None:

    gpdb_write.insert_gp(sample_gp)
    gp = gp_gpf_instance._gene_profile_db.get_gp("CHD8")

    assert gp is not None

    assert gp.gene_sets == [
        "main_CHD8 target genes",
    ]

    assert gp.gene_scores["autism_scores"] == {
        "SFARI gene score": {"value": 1.0, "format": "%s"},
        "RVIS_rank": {"value": 193.0, "format": "%s"},
        "RVIS": {"value": approx(-2.34), "format": "%s"},
    }

    assert gp.gene_scores["protection_scores"] == {
        "SFARI gene score": {"value": 1.0, "format": "%s"},
        "RVIS_rank": {"value": 193.0, "format": "%s"},
        "RVIS": {"value": approx(-2.34), "format": "%s"},
    }

    assert gp.variant_counts == {
        "iossifov_2014": {
            "autism": {
                "denovo_missense": {"count": 21, "rate": 2},
                "denovo_noncoding": {"count": 53, "rate": 1},
            },
            "unaffected": {
                "denovo_missense": {"count": 51, "rate": 4},
                "denovo_noncoding": {"count": 43, "rate": 3},
            },
        },
    }


def test_gpdb_sort(
        gp_gpf_instance: GPFInstance,
        gpdb_write: GeneProfileDBWriter,
        sample_gp: GPStatistic) -> None:
    gpdb_write.insert_gp(sample_gp)
    sample_gp.gene_symbol = "CHD7"
    sample_scores = sample_gp.gene_scores
    sample_scores["protection_scores"]["SFARI gene score"] = -11
    gpdb_write.insert_gp(sample_gp)
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


def test_gpdb_symbol_search(
        gp_gpf_instance: GPFInstance,
        gpdb_write: GeneProfileDBWriter,
        sample_gp: GPStatistic) -> None:
    gpdb_write.insert_gp(sample_gp)
    sample_gp.gene_symbol = "CHD7"
    gpdb_write.insert_gp(sample_gp)
    sample_gp.gene_symbol = "TESTCHD"
    gpdb_write.insert_gp(sample_gp)

    all_symbols = gp_gpf_instance._gene_profile_db.list_symbols(1)
    assert len(all_symbols) == 3
    assert all_symbols[0] == "CHD7"
    assert all_symbols[-1] == "TESTCHD"

    all_symbols = gp_gpf_instance._gene_profile_db.list_symbols(1, "CHD")
    assert len(all_symbols) == 2
    assert all_symbols[0] == "CHD7"
    assert all_symbols[-1] == "CHD8"

    all_symbols = gp_gpf_instance._gene_profile_db.list_symbols(1, "TEST")
    assert len(all_symbols) == 1
    assert all_symbols[0] == "TESTCHD"
