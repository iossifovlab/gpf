'''
Created on Apr 3, 2018

@author: lubo
'''


def test_denovo_get_gene_set_sd_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set('denovo', 'LGDs', {'SD': ['autism', 'epilepsy']})
    assert lgds is not None
    assert lgds['count'] == 576
    assert lgds['name'] == 'LGDs'
    assert lgds['desc'] == 'LGDs (SD:autism,epilepsy)'


def test_denovo_get_gene_set_sd_denovo_db_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs',
        {
            'SD': ['autism', 'epilepsy'],
            'denovo_db': ['autism', 'epilepsy'],
        })
    assert lgds is not None
    assert lgds['count'] == 614
    assert lgds['name'] == 'LGDs'
    assert lgds['desc'] == \
        'LGDs (SD:autism,epilepsy;denovo_db:autism,epilepsy)'
