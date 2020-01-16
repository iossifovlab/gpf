'''
Created on Apr 10, 2017

@author: lubo
'''
from dae.configuration.config_parser_base import ConfigParserBase
from dae.pheno_browser.prepare_data import PreparePhenoBrowserBase


def test_pheno_regressions_from_conf_path(regressions_conf):
    regs = ConfigParserBase.read_file_configuration(regressions_conf, '')
    expected_regs = {
        'reg1': {
            'instrument_name': 'i1',
            'measure_name': 'regressor1',
            'jitter': '0.1',
            'work_dir': '',
            'wd': ''
        },
        'reg2': {
            'instrument_name': 'i1',
            'measure_name': 'regressor2',
            'jitter': '0.2',
            'work_dir': '',
            'wd': ''
        },
        'reg3': {
            'instrument_name': '',
            'measure_name': 'common_regressor',
            'jitter': '0.3',
            'work_dir': '',
            'wd': ''
        },
        'reg4': {
            'instrument_name': 'i2',
            'measure_name': 'regressor1',
            'jitter': '0.4',
            'work_dir': '',
            'wd': ''
        },
    }

    assert len(regs.regression) == len(expected_regs)

    for reg_name, expected_reg in expected_regs.items():
        assert reg_name in regs.regression
        assert regs.regression[reg_name] == expected_reg


def test_has_regression_measure(
        fake_phenotype_data, output_dir, regressions_conf):
    reg = ConfigParserBase.read_file_configuration(regressions_conf, '')
    prep = PreparePhenoBrowserBase(
        'fake', fake_phenotype_data, output_dir, reg
    )

    expected_reg_measures = [
     ('regressor1', 'i1'),
     ('regressor2', 'i1'),
     ('common_regressor', ''),
     ('common_regressor', 'i1'),
     ('common_regressor', 'i2'),
     ('regressor1', 'i2')
    ]

    for e in expected_reg_measures:
        assert prep._has_regression_measure(*e)
