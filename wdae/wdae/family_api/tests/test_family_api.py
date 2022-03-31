import pytest
from rest_framework import status  # type: ignore
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


def test_list_families_view_nonexistent(admin_client):
    url = "/api/v3/families/Study123123123"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_family_details_view(admin_client):
    url = "/api/v3/families/Study1/f6"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "family_id": "f6",
        "family_type": "TRIO",
        "person_ids": ["mom6", "dad6", "ch6"],
        "samples_index": None
    }


def test_family_details_view_nonexistent(admin_client):
    url = "/api/v3/families/Study1/f654654654"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_members_view(admin_client):
    url = "/api/v3/families/Study1/f6/members"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == ["mom6", "dad6", "ch6"]


def test_list_members_view_nonexistent(admin_client):
    url = "/api/v3/families/Study1/f654654654/members"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_member_details_view(admin_client):
    url = "/api/v3/families/Study1/f6/members/ch6"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "person_id": "ch6",
        "family_id": "f6",
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


def test_member_details_view_nonexistent(admin_client):
    url = "/api/v3/families/Study1/f6/members/ch456456"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_full_family_details_view(admin_client):
    url = "/api/v3/families/Study1/f6/members/all"

    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 3
    assert response.data[0] == {
        "person_id": "mom6",
        "family_id": "f6",
        "dad_id": None,
        "mom_id": None,
        "sample_id": "mom6",
        "index": 0,
        "sex": str(Sex.female),
        "role": str(Role.mom),
        "status": str(Status.unaffected),
        "layout": None,
        "generated": None,
        "family_bin": None,
        "not_sequenced": None,
        "missing": False,
    }
    assert response.data[1] == {
        "person_id": "dad6",
        "family_id": "f6",
        "dad_id": None,
        "mom_id": None,
        "sample_id": "dad6",
        "index": 1,
        "sex": str(Sex.male),
        "role": str(Role.dad),
        "status": str(Status.unaffected),
        "layout": None,
        "generated": None,
        "family_bin": None,
        "not_sequenced": None,
        "missing": False,
    }
    assert response.data[2] == {
        "person_id": "ch6",
        "family_id": "f6",
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


def test_full_study_families_view(admin_client):
    url = "/api/v3/families/Study1/all"

    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 10
    f6_idx = -1
    for idx, fam in enumerate(response.data):
        if fam["family_id"] == "f6":
            f6_idx = idx
            break
    f6 = response.data[f6_idx]
    assert f6["family_id"] == "f6"
    assert f6["family_type"] == "TRIO"
    assert f6["person_ids"] == ["mom6", "dad6", "ch6"]
    assert len(f6["members"]) == 3
    assert f6["members"][2] == {
        "person_id": "ch6",
        "family_id": "f6",
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
