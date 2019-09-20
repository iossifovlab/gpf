import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from users_api.models import WdaeUser


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


@pytest.fixture(scope='function')
def mock_genomes_db(mocker):
    genome = mocker.Mock()
    genome.getSequence = lambda _, start, end: 'A' * (end - start + 1)

    mocker.patch(
        'dae.GenomesDB.GenomesDB.__init__', return_value=None
    )

    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_genome',
        return_value=genome
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_gene_models',
        return_value='Gene Models'
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_genome_file',
        return_value='./genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa'
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_gene_model_id',
        return_value='RefSeq2013'
    )
