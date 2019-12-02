import pytest

import tempfile
import shutil
import os


from dae.configuration.dae_config_parser import DAEConfigParser

from dae.pheno.pheno_factory import PhenoDb


def relative_to_this_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def output_dir(request):
    tmpdir = tempfile.mkdtemp(prefix='pheno_browser')

    def fin():
        shutil.rmtree(tmpdir)

    request.addfinalizer(fin)
    return tmpdir


@pytest.fixture(scope='session')
def dae_config_fixture():
    return DAEConfigParser.read_and_parse_file_configuration(
        work_dir=relative_to_this_folder('fixtures')
    )


@pytest.fixture(scope='session')
def fake_pheno_db(dae_config_fixture):
    return PhenoDb(dae_config_fixture)


@pytest.fixture(scope='session')
def fake_phenotype_data(fake_pheno_db):
    db = fake_pheno_db.get_phenotype_data('fake')
    return db


@pytest.fixture(scope='session')
def fake_phenotype_data_browser_dir():
    return relative_to_this_folder(
        'fixtures/pheno/fake_phenoDB/fake_browser.db')


@pytest.fixture(scope='session')
def fake_phenotype_data_desc_conf():
    return relative_to_this_folder('fixtures/pheno/fake_phenoDB/fake.conf')


@pytest.fixture(scope='session')
def regressions_conf():
    return relative_to_this_folder('fixtures/regressions.conf')
