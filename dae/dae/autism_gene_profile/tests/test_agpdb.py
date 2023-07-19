# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import box

from sqlalchemy import inspect
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.gpf_instance import GPFInstance


def test_agpdb_table_building(
    tmp_path: pathlib.Path,
    agp_config: box.Box
) -> None:
    agpdb_filename = str(tmp_path / "agpdb")
    agpdb = AutismGeneProfileDB(
        agp_config,
        agpdb_filename
    )
    inspector = inspect(agpdb.engine)

    cols = []
    for column in inspector.get_columns("autism_gene_profile"):
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
            "autism_scores_SFARI_gene_score",
            "protection_scores_RVIS",
            "protection_scores_RVIS_rank",
            "protection_scores_SFARI_gene_score",
            "iossifov_we2014_test_unaffected_denovo_missense_rate",
            "iossifov_we2014_test_unaffected_denovo_missense",
            "iossifov_we2014_test_unaffected_denovo_noncoding_rate",
            "iossifov_we2014_test_unaffected_denovo_noncoding",
            "iossifov_we2014_test_unknown_denovo_missense_rate",
            "iossifov_we2014_test_unknown_denovo_missense",
            "iossifov_we2014_test_unknown_denovo_noncoding_rate",
            "iossifov_we2014_test_unknown_denovo_noncoding",
        ])
    ) == set()


def test_agpdb_insert_and_get_agp(
        tmp_path: pathlib.Path,
        agp_gpf_instance: GPFInstance,
        sample_agp: AGPStatistic,
        agp_config: box.Box) -> None:

    agpdb_filename = str(tmp_path / "agpdb")
    agpdb = AutismGeneProfileDB(
        agp_config, agpdb_filename, clear=True)
    agpdb.insert_agp(sample_agp)
    agp = agpdb.get_agp("CHD8")

    assert agp is not None

    assert agp.gene_sets == [
        "main_CHD8 target genes"
    ]

    assert agp.genomic_scores["autism_scores"] == {
        "SFARI_gene_score": {"value": 1.0, "format": "%s"},
        "RVIS_rank": {"value": 193.0, "format": "%s"},
        "RVIS": {"value": -2.34, "format": "%s"}
    }

    assert agp.genomic_scores["protection_scores"] == {
        "SFARI_gene_score": {"value": 1.0, "format": "%s"},
        "RVIS_rank": {"value": 193.0, "format": "%s"},
        "RVIS": {"value": -2.34, "format": "%s"}
    }

    assert agp.variant_counts == {
        "iossifov_we2014_test": {
            "unknown": {
                "denovo_noncoding": {"count": 53, "rate": 1},
                "denovo_missense": {"count": 21, "rate": 2}
            },
            "unaffected": {
                "denovo_noncoding": {"count": 43, "rate": 3},
                "denovo_missense": {"count": 51, "rate": 4}
            },
        }
    }


def test_agpdb_sort(
        agp_gpf_instance: GPFInstance,
        sample_agp: AGPStatistic) -> None:
    sample_agp.gene_symbol = "CHD7"
    sample_scores = sample_agp.genomic_scores
    sample_scores["protection_scores"]["SFARI_gene_score"] = -11
    agp_gpf_instance._autism_gene_profile_db.insert_agp(sample_agp)
    stats_unsorted = agp_gpf_instance.query_agp_statistics(1)
    stats_sorted = agp_gpf_instance.query_agp_statistics(
        1, sort_by="protection_scores_SFARI_gene_score", order="asc"
    )
    assert stats_unsorted[0]["geneSymbol"] == "CHD8"
    assert stats_unsorted[1]["geneSymbol"] == "CHD7"

    assert stats_sorted[0]["geneSymbol"] == "CHD7"
    assert stats_sorted[1]["geneSymbol"] == "CHD8"

    stats_sorted = agp_gpf_instance.query_agp_statistics(
        1, sort_by="autism_scores_SFARI_gene_score", order="desc"
    )
    stats_sorted = agp_gpf_instance.query_agp_statistics(
        1,
        sort_by="iossifov_we2014_test_unknown_denovo_noncoding", order="desc"
    )
    stats_sorted = agp_gpf_instance.query_agp_statistics(
        1, sort_by="main_CHD8 target genes", order="desc"
    )
