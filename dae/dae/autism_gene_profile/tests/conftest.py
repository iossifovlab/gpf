from dae.gpf_instance.gpf_instance import GPFInstance
from dae.autism_gene_profile.statistic import AGPStatistic
import pytest
import tempfile
import os

from box import Box


@pytest.fixture
def temp_dbfile(request):
    dbfile = tempfile.mktemp(prefix="dbfile_")

    def fin():
        if os.path.exists(dbfile):
            os.remove(dbfile)

    request.addfinalizer(fin)
    return dbfile


@pytest.fixture
def agp_gpf_instance(fixtures_gpf_instance, mocker):
    agp_config = Box({
        'gene_symbols': ['PLEKHN1', 'SAMD11'],
        'protection_scores': ['SFARI_gene_score', 'RVIS_rank', 'RVIS'],
        'autism_scores': ['SFARI_gene_score', 'RVIS_rank', 'RVIS'],
        'datasets': Box({
            'f1_study': Box({
                'effects': ['synonymous', 'missense'],
                'person_sets': [
                    Box({
                        'set_name': 'phenotype1',
                        'collection_name': 'phenotype'
                    }),
                    Box({
                        'set_name': 'unaffected',
                        'collection_name': 'phenotype'
                    }),
                ]
            })
        })
    })
    mocker.patch.object(
        GPFInstance,
        "_autism_gene_profile_config",
        return_value=agp_config,
        new_callable=mocker.PropertyMock
    )
    main_gene_sets = {
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
    mocker.patch.object(
        fixtures_gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets
    )
    return fixtures_gpf_instance


@pytest.fixture(scope="session")
def sample_agp():
    gene_sets = [
        'FMRP Tuschl', 'autism candidates from Iossifov PNAS 2015',
        'autism candidates from Sanders Neuron 2015', 'essential genes'
    ]
    protection_scores = {
        'SFARI_gene_score': 1, 'RVIS_rank': 193.0, 'RVIS': -2.34
    }
    autism_scores = {
        'SFARI_gene_score': 1, 'RVIS_rank': 193.0, 'RVIS': -2.34
    }
    variant_counts = {
        'f1_study': {
            'affected': {'LGDS': 53, 'missense': 21, 'intron': 10},
            'unaffected': {'LGDS': 43, 'missense': 51, 'intron': 70},
        }
    }
    return AGPStatistic(
        "CHD8", gene_sets, protection_scores, autism_scores, variant_counts
    )
