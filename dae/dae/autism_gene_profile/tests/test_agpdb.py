from dae.autism_gene_profile.db import AutismGeneProfileDB
from sqlalchemy import inspect


def test_agpdb_tables_building(temp_dbfile, agp_gpf_instance):
    agpdb = AutismGeneProfileDB(temp_dbfile)
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
            "id", "set_name"
        ])
    ) == set()
    assert set(table_columns["gene_symbol_sets"]).difference(
        set([
            "id", "symbol_id", "set_id", "present"
        ])
    ) == set()
    assert set(table_columns["autism_scores"]).difference(
        set([
            "id", "symbol_id", "score_name", "score_value"
        ])
    ) == set()
    assert set(table_columns["protection_scores"]).difference(
        set([
            "id", "symbol_id", "score_name", "score_value"
        ])
    ) == set()
    assert set(table_columns["variant_counts"]).difference(
        set([
            "id", "symbol_id", "study_id", "people_group",
            "effect_type", "count"
        ])
    ) == set()
    assert set(table_columns["studies"]).difference(
        set([
            "id", "study_id"
        ])
    ) == set()
    print(table_columns)


def test_agpdb_get_studies(temp_dbfile, agp_gpf_instance):
    agpdb = AutismGeneProfileDB(temp_dbfile)
    agpdb.populate_data_tables(agp_gpf_instance)
    study_ids = agpdb._get_study_ids().keys()
    assert len(study_ids) == 40


def test_agpdb_get_gene_sets(temp_dbfile, agp_gpf_instance):
    agpdb = AutismGeneProfileDB(temp_dbfile)
    agpdb.populate_data_tables(agp_gpf_instance)
    gene_sets = set([gs[1] for gs in agpdb._get_gene_sets()])
    expected = {
        'CHD8 target genes',
        'FMRP Darnell',
        'FMRP Tuschl',
        'PSD',
        'autism candidates from Iossifov PNAS 2015',
        'autism candidates from Sanders Neuron 2015',
        'brain critical genes',
        'brain embryonically expressed',
        'chromatin modifiers',
        'essential genes',
        'non-essential genes',
        'postsynaptic inhibition',
        'synaptic clefts excitatory',
        'synaptic clefts inhibitory',
        'topotecan downreg genes'
    }
    assert gene_sets.difference(expected) == set()


def test_agpdb_insert_and_get_agp(temp_dbfile, agp_gpf_instance, sample_agp):
    agpdb = AutismGeneProfileDB(temp_dbfile)
    agpdb.populate_data_tables(agp_gpf_instance)
    agpdb.insert_agp(sample_agp)
    agp = agpdb.get_agp("CHD8")
    assert agp.gene_sets == [
        'CHD8 target genes'
    ]

    assert agp.protection_scores == {
        'SFARI_gene_score': 1, 'RVIS_rank': 193.0, 'RVIS': -2.34
    }

    assert agp.autism_scores == {
        'SFARI_gene_score': 1, 'RVIS_rank': 193.0, 'RVIS': -2.34
    }

    assert agp.variant_counts == {
        'f1_study': {
            'affected': {'LGDS': 53, 'missense': 21, 'intron': 10},
            'unaffected': {'LGDS': 43, 'missense': 51, 'intron': 70},
        }
    }
