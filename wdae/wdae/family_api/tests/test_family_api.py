# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import json
from rest_framework import status  # type: ignore
from dae.variants.attributes import Sex, Role, Status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/families/Study1", "get", None),
    ("/api/v3/families/Study1/f6", "get", None),
    ("/api/v3/families/Study1/f6/members", "get", None),
    ("/api/v3/families/Study1/f6/members/ch6", "get", None),
    ("/api/v3/families/Study1/f6/members/all", "get", None),
    ("/api/v3/families/Study1/all", "get", None),
])
def test_family_api_permissions(anonymous_client, url, method, body):
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json"
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_families_view(admin_client):
    url = "/api/v3/families/Study1"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert list(response.data) == [
        "f1", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11"
    ]


def test_list_families_view_tag_filter(admin_client):
    url = "/api/v3/families/Study1?tags=tag_male_prb_family"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == set([
        "f6", "f9", "f10"
    ])


def test_list_families_view_tag_filter_multiple(admin_client):
    url = "/api/v3/families/Study1?tags=tag_nuclear_family,tag_trio_family"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == set([
        "f1", "f3", "f5", "f6", "f7", "f8", "f11"
    ])


def test_list_families_view_nonexistent(admin_client):
    url = "/api/v3/families/Study123123123"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_tags_view(admin_client):
    url = "/api/v3/families/tags"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == set([
        "tag_nuclear_family",
        "tag_quad_family",
        "tag_trio_family",
        "tag_simplex_family",
        "tag_multiplex_family",
        "tag_control_family",
        "tag_affected_dad_family",
        "tag_affected_mom_family",
        "tag_affected_prb_family",
        "tag_affected_sib_family",
        "tag_unaffected_dad_family",
        "tag_unaffected_mom_family",
        "tag_unaffected_prb_family",
        "tag_unaffected_sib_family",
        "tag_male_prb_family",
        "tag_female_prb_family",
        "tag_missing_mom_family",
        "tag_missing_dad_family"
    ])


def test_family_details_view(admin_client):
    url = "/api/v3/families/Study1/f6"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "family_id": "f6",
        "family_type": "TRIO",
        "person_ids": ["mom6", "dad6", "ch6"],
        "samples_index": None,
        "tags": set([
            "tag_affected_prb_family",
            "tag_family_type:type#3",
            "tag_male_prb_family",
            "tag_nuclear_family",
            "tag_simplex_family",
            "tag_trio_family",
            "tag_unaffected_dad_family",
            "tag_unaffected_mom_family"
        ])
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
    family = response.data[f6_idx]
    assert family["family_id"] == "f6"
    assert family["family_type"] == "TRIO"
    assert family["person_ids"] == ["mom6", "dad6", "ch6"]
    assert len(family["members"]) == 3
    assert family["members"][2] == {
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
