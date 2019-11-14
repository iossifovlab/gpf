import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.impala.parquet_io import ParquetManager


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='function')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=relative_to_this_test_folder('fixtures'))


@pytest.fixture(scope='function')
def dae_config_fixture(gpf_instance):
    return gpf_instance.dae_config


@pytest.fixture(scope='function')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def parquet_manager(dae_config_fixture):
    return ParquetManager(dae_config_fixture.studies_db.dir)

