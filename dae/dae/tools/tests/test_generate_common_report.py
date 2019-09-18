import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.tools.generate_common_report import main


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


def test_generate_common_report(gpf_instance):
    main(gpf_instance, argv=['--studies', ' '])
    main(gpf_instance, argv=['--show-studies'])
