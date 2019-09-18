import pytest

import tempfile
import shutil
import os

from dae.gpf_instance.gpf_instance import GPFInstance


def relative_to_this_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture
def output_dir(request):
    tmpdir = tempfile.mkdtemp(prefix='pheno_browser')

    def fin():
        shutil.rmtree(tmpdir)

    request.addfinalizer(fin)
    return tmpdir


@pytest.fixture(scope='session')
def fake_pheno_factory(gpf_instance):
    return gpf_instance.pheno_factory


@pytest.fixture(scope='session')
def fphdb(fake_pheno_factory):
    db = fake_pheno_factory.get_pheno_db('fake')
    return db


@pytest.fixture(scope='session')
def fphdb_browser_dir():
    return relative_to_this_folder(
        'fixtures/pheno/fake_phenoDB/fake_browser.db')


@pytest.fixture(scope='session')
def fphdb_desc_conf():
    return relative_to_this_folder('fixtures/pheno/fake_phenoDB/fake.conf')


@pytest.fixture(scope='session')
def regressions_conf():
    return relative_to_this_folder('fixtures/regressions.conf')
