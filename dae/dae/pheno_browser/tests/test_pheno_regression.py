'''
Created on Apr 10, 2017

@author: lubo
'''
from __future__ import unicode_literals
from dae.pheno.pheno_regression import PhenoRegressions


def test_pheno_regressions_from_conf_path(regressions_conf):
    regs = PhenoRegressions(regressions_conf)
    expected_regs = {
        'reg1': {'instrument_name': 'i1',
                 'measure_name': 'regressor1',
                 'jitter': '0.1'},
        'reg2': {'instrument_name': 'i1',
                 'measure_name': 'regressor2',
                 'jitter': '0.2'},
        'reg3': {'instrument_name': '',
                 'measure_name': 'common_regressor',
                 'jitter': '0.3'},
        'reg4': {'instrument_name': 'i2',
                 'measure_name': 'regressor1',
                 'jitter': '0.4'},
    }

    for reg_name, expected_reg in expected_regs.items():
        assert reg_name in regs
        assert regs[reg_name] == expected_reg


def test_pheno_regressions_has_measure(regressions_conf):
    regs = PhenoRegressions(regressions_conf)
    expected_reg_measures = [
     ('regressor1', 'i1'),
     ('regressor2', 'i1'),
     ('common_regressor', ''),
     ('common_regressor', 'i1'),
     ('common_regressor', 'i2'),
     ('regressor1', 'i2')
    ]

    for e in expected_reg_measures:
        assert regs.has_measure(*e)
