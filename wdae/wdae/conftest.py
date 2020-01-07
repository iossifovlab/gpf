import pytest
import os
from _pytest.monkeypatch import MonkeyPatch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from users_api.models import WdaeUser

from dae.gpf_instance.gpf_instance import GPFInstance
from gpf_instance.gpf_instance import reload_datasets


pytest_plugins = ['dae_conftests.dae_conftests']


@pytest.fixture(scope='session')
def monkeysession(request):
    mp = MonkeyPatch()
    request.addfinalizer(mp.undo)
    return mp


@pytest.fixture()
def user(db):
    User = get_user_model()
    u = User.objects.create(
        email="user@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False)
    u.set_password("secret")
    u.save()

    return u


@pytest.fixture()
def user_without_password(db):
    User = get_user_model()
    u = User.objects.create(
        email="user_without_password@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False)
    u.save()

    return u


@pytest.fixture()
def admin(db):
    User = get_user_model()
    u = User.objects.create(
        email="admin@example.com",
        name="User",
        is_staff=True,
        is_active=True,
        is_superuser=True)
    u.set_password("secret")
    u.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    u.groups.add(admin_group)

    return u


@pytest.fixture()
def user_client(user, client):
    client.login(email=user.email, password="secret")
    return client


@pytest.fixture()
def admin_client(admin, client):
    client.login(email=admin.email, password="secret")
    return client


@pytest.fixture(scope='session')
def global_gpf_instance():
    return GPFInstance()


@pytest.fixture(scope='session')
def default_gene_models(global_gpf_instance):
    return global_gpf_instance.genomes_db.get_gene_models()


@pytest.fixture(scope='session')
def default_genome(global_gpf_instance):
    return global_gpf_instance.genomes_db.get_genome()


@pytest.fixture(scope='session')
def mock_genomes_db(monkeysession, default_gene_models, default_genome):

    def fake_init(self, dae_dir, conf_file=None):
        self.dae_dir = None
        self.config = None

    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.__init__', fake_init
    )

    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_genome',
        lambda self: default_genome
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_genome_from_file',
        lambda self, _=None: default_genome
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_gene_models',
        lambda self, _=None: default_gene_models
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_genome_file',
        lambda self, _=None:
            './genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa'
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_gene_model_id',
        lambda self: 'RefSeq2013'
    )


def global_fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'tests', 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=global_fixtures_dir())


@pytest.fixture(scope='function')
def mock_gpf_instance(db, mocker, gpf_instance):
    reload_datasets(gpf_instance._variants_db)
    mocker.patch(
        'query_base.query_base.get_gpf_instance',
        return_value=gpf_instance
    )
