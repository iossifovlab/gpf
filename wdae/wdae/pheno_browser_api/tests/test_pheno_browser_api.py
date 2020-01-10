import pytest


pytestmark = pytest.mark.usefixtures('wdae_gpf_instance', 'calc_gene_sets')


URL = '/api/v3/pheno_browser/instruments'
MEASURES_URL = '/api/v3/pheno_browser/measures'
DOWNLOAD_URL = '/api/v3/pheno_browser/download'


def test_instruments_missing_dataset_id(admin_client):
    response = admin_client.get(URL)

    assert response.status_code == 400


def test_instruments_missing_dataset_id_forbidden(user_client):
    response = user_client.get(URL)

    assert response.status_code == 400


def test_instruments(admin_client):
    url = '{}?dataset_id=quads_f1_ds'.format(URL)
    response = admin_client.get(url)

    assert response.status_code == 200
    assert 'default' in response.data
    assert 'instruments' in response.data
    assert len(response.data['instruments']) == 1


def test_instruments_forbidden(user_client):
    url = '{}?dataset_id=quads_f1_ds'.format(URL)
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert header['detail'] == \
        'You do not have permission to perform this action.'


def test_measures(admin_client):
    url = '{}?dataset_id=quads_f1_ds&instrument=instrument1'.format(
        MEASURES_URL)
    response = admin_client.get(url)

    assert response.status_code == 200
    assert 'base_image_url' in response.data
    assert 'measures' in response.data
    assert 'has_descriptions' in response.data
    assert len(response.data['measures']) == 4


def test_measures_forbidden(user_client, user):
    print(user.groups.all())
    url = '{}?dataset_id=quads_f1_ds&instrument=instrument1'.format(
        MEASURES_URL)
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert header['detail'] == \
        'You do not have permission to perform this action.'


def test_download(admin_client):
    url = '{}?dataset_id=quads_f1_ds&instrument=instrument1'.format(
        DOWNLOAD_URL)
    response = admin_client.get(url)

    assert response.status_code == 200

    header = response.content.decode('utf-8').split()[0].split(',')
    assert header[0] == 'person_id'


def test_download_forbidden(user_client):
    url = '{}?dataset_id=quads_f1_ds&instrument=instrument1'.format(
        DOWNLOAD_URL)
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert header['detail'] == \
        'You do not have permission to perform this action.'


def test_download_all_instruments(admin_client):
    url = '{}?dataset_id=quads_f1_ds&instrument='.format(DOWNLOAD_URL)
    response = admin_client.get(url)

    assert response.status_code == 200

    header = response.content.decode('utf-8').split()[0].split(',')

    print('header:\n', header)
    assert len(header) == 5
    assert set(header) == {
        'person_id',
        'instrument1.continuous',
        'instrument1.categorical',
        'instrument1.ordinal',
        'instrument1.raw',
    }
