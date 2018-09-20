'''
Created on Apr 3, 2018

@author: lubo
'''
from __future__ import unicode_literals


def test_denovo_get_gene_set_sd_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs', {'SD_TEST': ['autism', 'epilepsy']})
    assert lgds is not None
    assert lgds['count'] == 576
    assert lgds['name'] == 'LGDs'
    assert lgds['desc'] == 'LGDs (SD_TEST:autism,epilepsy)'


def test_denovo_get_gene_set_sd_denovo_db_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs',
        {
            'SD_TEST': ['autism', 'epilepsy'],
            'denovo_db': ['autism', 'epilepsy'],
        })
    assert lgds is not None
    assert lgds['count'] == 597
    assert lgds['name'] == 'LGDs'
    #     assert lgds['desc'] == \
    #         'LGDs (SD:autism,epilepsy;denovo_db:autism,epilepsy)'
    assert "SD_TEST:autism,epilepsy" in lgds['desc']
    assert "denovo_db:autism,epilepsy" in lgds['desc']
