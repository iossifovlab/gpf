import pytest

from dae.pheno.utils.config import PhenoRegressionConfigParser
from dae.pheno.tests.conftest import relative_to_this_folder


def test_load_valid_regression_config():
    path = relative_to_this_folder(
        'fixtures/regression_configs/sample_regression_config.conf')

    config = PhenoRegressionConfigParser.\
        read_and_parse_file_configuration(path, '')

    assert config
    assert config['regression']
    assert list(config['regression'].keys()) == \
        ['sample_reg_one', 'sample_reg_two']

    assert 'sample_reg_one' in config.regression
    assert config.regression.sample_reg_one.instrument_name == \
        'sample_instrument'
    assert config.regression.sample_reg_one.measure_name == \
        'sample_measure'
    assert config.regression.sample_reg_one.display_name == \
        'sample_display_name'
    assert config.regression.sample_reg_one.jitter == \
        0.1

    assert 'sample_reg_two' in config.regression
    assert config.regression.sample_reg_two.instrument_name == \
        'sample_instrument_2'
    assert config.regression.sample_reg_two.measure_name == \
        'sample_measure_2'
    assert config.regression.sample_reg_two.display_name == \
        'sample_display_name_2'
    assert config.regression.sample_reg_two.jitter == \
        0.2


def test_load_valid_embedded_regression_config():
    path = relative_to_this_folder(
        'fixtures/regression_configs/embedded_regression_config.conf')

    config = PhenoRegressionConfigParser.\
        read_and_parse_file_configuration(path, '')

    assert config
    assert config['regression']
    assert list(config['regression'].keys()) == \
        ['sample_reg_one', 'sample_reg_two']

    assert 'sample_reg_one' in config.regression
    assert config.regression.sample_reg_one.instrument_name == \
        'sample_instrument'
    assert config.regression.sample_reg_one.measure_name == \
        'sample_measure'
    assert config.regression.sample_reg_one.display_name == \
        'sample_display_name'
    assert config.regression.sample_reg_one.jitter == \
        0.1

    assert 'sample_reg_two' in config.regression
    assert config.regression.sample_reg_two.instrument_name == \
        'sample_instrument_2'
    assert config.regression.sample_reg_two.measure_name == \
        'sample_measure_2'
    assert config.regression.sample_reg_two.display_name == \
        'sample_display_name_2'
    assert config.regression.sample_reg_two.jitter == \
        0.2


def test_load_empty_regression_config():
    path = relative_to_this_folder(
        'fixtures/regression_configs/empty_regression_config.conf')
    with pytest.raises(AssertionError) as excinfo:
        PhenoRegressionConfigParser.read_and_parse_file_configuration(path, '')

    assert str(excinfo.value) == \
        '{} is not a valid regression config!'.format(path)


@pytest.mark.parametrize('config', [
    ('invalid_regression_config_a.conf'),
    ('invalid_regression_config_b.conf'),
    ('invalid_regression_config_c.conf'),
    ('invalid_regression_config_d.conf'),
])
def test_load_invalid_regression_configs(config):
    path = relative_to_this_folder(
        'fixtures/regression_configs/{}'.format(config))

    with pytest.raises(AssertionError) as excinfo:
        PhenoRegressionConfigParser.read_and_parse_file_configuration(path, '')
    assert str(excinfo.value) == \
        ('{} is not a valid regression config!'
         ' The section "sample_reg_one" is invalid!').format(path)
