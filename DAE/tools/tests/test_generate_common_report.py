import pytest

import os

from configuration.configuration import DAEConfig
from tools.generate_common_report import main


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig.make_config(fixtures_dir())
    return dae_config


def test_generate_common_report(dae_config_fixture):
    main(dae_config_fixture, argv=['--studies', ' '])
    main(dae_config_fixture, argv=['--show-studies'])
