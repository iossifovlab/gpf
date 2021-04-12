import pytest
from rest_framework import status
from dae.variants.attributes import Sex, Role, Status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_list_families_view(admin_client):
    url = "/api/v3/families/Study1"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert list(response.data) == [
        "f1", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11"
    ]


def test_family_details_view(admin_client):
    url = "/api/v3/families/Study1/f6"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "family_id": "f6",
        "person_ids": ["mom6", "dad6", "ch6"],
        "samples_index": None
    }


def test_list_members_view(admin_client):
    url = "/api/v3/families/Study1/f6/members"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == ["mom6", "dad6", "ch6"]


def test_member_details_view(admin_client):
    url = "/api/v3/families/Study1/f6/members/ch6"
    response = admin_client.get(url)
    print(response.data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "person_id": "ch6",
        "dad_id": "dad6",
        "mom_id": "mom6",
        "sample_id": "ch6",
        "index": 2,
        "sex": str(Sex.male),
        "role": str(Role.prb),
        "status": str(Status.affected),
        "layout": None,
        "generated": None,
        "family_bin": None,
        "not_sequenced": None,
        "missing": False,
    }
