import pytest

import os

from dae.configuration.configuration import DAEConfig
from dae.tools.generate_common_report import main


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig.read_and_parse_file_configuration(
        work_dir=fixtures_dir())
    return dae_config


def test_generate_common_report(dae_config_fixture):
    main(dae_config_fixture, argv=['--studies', ' '])
    main(dae_config_fixture, argv=['--show-studies'])
