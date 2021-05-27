from dae.autism_gene_profile.db import AutismGeneProfileDB
from sqlalchemy import inspect


def test_agpdb_tables_building(temp_dbfile, agp_config):
    agpdb = AutismGeneProfileDB(
        agp_config,
        temp_dbfile
    )
    inspector = inspect(agpdb.engine)

    table_columns = dict()

    for table in inspector.get_table_names():
        cols = []
        for column in inspector.get_columns(table):
            cols.append(column["name"])
        table_columns[table] = cols
    assert set(table_columns["gene_symbols"]).difference(
        set([
            "id", "symbol_name"
        ])
    ) == set()
    assert set(table_columns["gene_sets"]).difference(
        set([
            "id", "set_id", "collection_id"
        ])
    ) == set()
    assert set(table_columns["gene_symbol_sets"]).difference(
        set([
            "id", "symbol_id", "set_id", "present"
        ])
    ) == set()
    assert set(table_columns["genomic_scores"]).difference(
        set([
            "id", "symbol_id", "score_name", "score_value", "score_category"
        ])
    ) == set()
    assert set(table_columns["variant_counts"]).difference(
        set([
            "id", "symbol_id", "study_id", "people_group",
            "statistic_id", "count", "rate"
        ])
    ) == set()
    assert set(table_columns["studies"]).difference(
        set([
            "id", "study_id"
        ])
    ) == set()
    print(table_columns)


def test_agpdb_get_studies(temp_dbfile, agp_gpf_instance, agp_config):
    agpdb = AutismGeneProfileDB(
        agp_config,
        temp_dbfile
    )
    study_ids = agpdb._get_study_ids().keys()
    assert len(study_ids) == 41


def test_agpdb_get_gene_sets(temp_dbfile, agp_config, agp_gpf_instance):
    agpdb = AutismGeneProfileDB(agp_config, temp_dbfile)
    gene_sets = set([gs[1] for gs in agpdb._get_gene_sets()])
    expected = {
        'CHD8 target genes',
        'FMRP Darnell',
    }
    assert expected.difference(gene_sets) == set()
    assert gene_sets.difference(expected) == set()


def test_agpdb_insert_and_get_agp(
        temp_dbfile, agp_gpf_instance, sample_agp, agp_config):
    agpdb = AutismGeneProfileDB(agp_config, temp_dbfile, clear=True)
    agpdb.populate_data_tables(agp_gpf_instance.get_genotype_data_ids())
    agpdb.insert_agp(sample_agp)
    agp = agpdb.get_agp("CHD8")
    assert agp.gene_sets == [
        'CHD8 target genes'
    ]

    assert agp.genomic_scores["autism_scores"] == {
        'SFARI_gene_score': {'value': 1.0, 'format': '%s'},
        'RVIS_rank': {'value': 193.0, 'format': '%s'},
        'RVIS': {'value': -2.34, 'format': '%s'}
    }

    assert agp.genomic_scores["protection_scores"] == {
        'SFARI_gene_score': {'value': 1.0, 'format': '%s'},
        'RVIS_rank': {'value': 193.0, 'format': '%s'},
        'RVIS': {'value': -2.34, 'format': '%s'}
    }

    assert agp.variant_counts == {
        'iossifov_we2014_test': {
            'unknown': {
                'denovo_noncoding': {"count": 53, "rate": 1},
                'denovo_missense': {"count": 21, "rate": 2}
            },
            'unaffected': {
                'denovo_noncoding': {"count": 43, "rate": 3},
                'denovo_missense': {"count": 51, "rate": 4}
            },
        }
    }


def test_agpdb_sort(agp_gpf_instance, sample_agp):
    sample_agp.gene_symbol = "CHD7"
    sample_scores = sample_agp.genomic_scores
    sample_scores["protection_scores"]["SFARI_gene_score"] = -11
    agp_gpf_instance._autism_gene_profile_db.insert_agp(sample_agp)
    stats_unsorted = agp_gpf_instance.query_agp_statistics(1)
    stats_sorted = agp_gpf_instance.query_agp_statistics(
        1, sort_by="protection_scores_SFARI_gene_score", order="asc"
    )
    assert stats_unsorted[0].gene_symbol == "CHD8"
    assert stats_unsorted[1].gene_symbol == "CHD7"

    assert stats_sorted[0].gene_symbol == "CHD7"
    assert stats_sorted[1].gene_symbol == "CHD8"

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
