from dae.autism_gene_profile.statistic import AGPStatistic
import pytest


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
