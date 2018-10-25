'''
Created on Apr 3, 2018

@author: lubo
'''
from __future__ import unicode_literals
import pytest

pytestmark = pytest.mark.skip('depends on real data')


def test_denovo_get_gene_set_sd_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs', {'SD_TEST': ['autism', 'epilepsy']})
    assert lgds is not None
    # FIXME: changed after rennotation
    # assert lgds['count'] == 576
    assert lgds['count'] == 581
    assert lgds['name'] == 'LGDs'
    assert lgds['desc'] == 'LGDs (SD_TEST:autism,epilepsy)'


def test_denovo_get_gene_set_sd_denovo_db_lgds_autism_and_epilepsy(gscs):
    lgds = gscs.get_gene_set(
        'denovo', 'LGDs',
        {
            'SD_TEST': ['autism', 'epilepsy'],
            'TESTdenovo_db': ['autism', 'epilepsy'],
        })
    assert lgds is not None
    # FIXME: changed after rennotation
    # assert lgds['count'] == 597
    assert lgds['count'] == 602
    assert lgds['name'] == 'LGDs'

    assert "SD_TEST:autism,epilepsy" in lgds['desc']
    assert "TESTdenovo_db:autism,epilepsy" in lgds['desc']
