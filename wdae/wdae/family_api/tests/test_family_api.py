# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from unittest.mock import ANY

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

from dae.variants.attributes import Role, Sex, Status


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/families/t4c8_study_1", "get", None),
    ("/api/v3/families/t4c8_study_1/f1.1", "get", None),
    ("/api/v3/families/t4c8_study_1/f1.1/members", "get", None),
    ("/api/v3/families/t4c8_study_1/f1.1/members/dad1", "get", None),
    ("/api/v3/families/t4c8_study_1/f1.1/members/all", "get", None),
    ("/api/v3/families/t4c8_study_1/all", "get", None),
])
def test_family_api_permissions(
    anonymous_client: Client, url: str, method: str, body: dict | None,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_families_view(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert list(response.data) == ["f1.1", "f1.3"]  # type: ignore


def test_list_families_view_tag_filter(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1?tags=tag_female_prb_family"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "f1.1", "f1.3",
    }


def test_list_families_view_tag_filter_multiple(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1?tags=tag_nuclear_family,tag_trio_family"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "f1.1", "f1.3",
    }


def test_list_families_view_nonexistent(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/Study123123123"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_tags_view(
  admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/tags"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
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
        "tag_missing_dad_family",
    }


def test_family_details_view(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f1.3"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {  # type: ignore
        "family_id": "f1.3",
        "person_ids": ["mom3", "dad3", "p3", "s3"],
        "samples_index": None,
        "family_type": "other",
        "tags": {
            "tag_simplex_family",
            "tag_quad_family",
            "tag_unaffected_mom_family",
            "tag_unaffected_dad_family",
            "tag_female_prb_family",
            "tag_nuclear_family",
            "tag_affected_prb_family",
            "tag_unaffected_sib_family",
        },
    }


def test_family_details_view_nonexistent(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f654654654"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_members_view(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f1.3/members"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == ["mom3", "dad3", "p3", "s3"]  # type: ignore


def test_list_members_view_nonexistent(
  admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f654654654/members"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_member_details_view(
  admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f1.3/members/s3"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {  # type: ignore
        "family_id": "f1.3",
        "person_id": "s3",
        "dad_id": "dad3",
        "mom_id": "mom3",
        "sample_id": "s3",
        "member_index": 3,
        "sex": str(Sex.female),
        "role": str(Role.sib),
        "status": str(Status.unaffected),
        "layout": ANY,  # FIXME temporary handle field variying between two values
        "generated": False,
        "family_bin": None,
        "not_sequenced": False,
        "missing": False,
    }


def test_member_details_view_nonexistent(
  admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f6/members/ch456456"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_full_family_details_view(
  admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/f1.1/members/all"

    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 4  # type: ignore
    assert response.data[0] == {  # type: ignore
        "family_id": "f1.1",
        "person_id": "mom1",
        "dad_id": None,
        "mom_id": None,
        "sample_id": "mom1",
        "member_index": 0,
        "sex": str(Sex.female),
        "role": str(Role.mom),
        "status": str(Status.unaffected),
        "generated": False,
        "layout": ANY,  # FIXME temporary handle field variying between two values
        "family_bin": None,
        "not_sequenced": False,
        "missing": False,
    }
    assert response.data[1] == {  # type: ignore
        "family_id": "f1.1",
        "person_id": "dad1",
        "dad_id": None,
        "mom_id": None,
        "sample_id": "dad1",
        "member_index": 1,
        "sex": str(Sex.male),
        "role": str(Role.dad),
        "status": str(Status.unaffected),
        "layout": ANY,  # FIXME temporary handle field variying between two values
        "generated": False,
        "family_bin": None,
        "not_sequenced": False,
        "missing": False,
    }
    assert response.data[2] == {  # type: ignore
        "family_id": "f1.1",
        "person_id": "p1",
        "dad_id": "dad1",
        "mom_id": "mom1",
        "sample_id": "p1",
        "member_index": 2,
        "sex": str(Sex.female),
        "role": str(Role.prb),
        "status": str(Status.affected),
        "layout": ANY,  # FIXME temporary handle field variying between two values
        "generated": False,
        "family_bin": None,
        "not_sequenced": False,
        "missing": False,
    }
    assert response.data[3] == {  # type: ignore
        "family_id": "f1.1",
        "person_id": "s1",
        "dad_id": "dad1",
        "mom_id": "mom1",
        "sample_id": "s1",
        "member_index": 3,
        "sex": str(Sex.male),
        "role": str(Role.sib),
        "status": str(Status.unaffected),
        "layout": ANY,  # FIXME temporary handle field variying between two values
        "generated": False,
        "family_bin": None,
        "not_sequenced": False,
        "missing": False,
    }


def test_full_study_families_view(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/families/t4c8_study_1/all"

    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2  # type: ignore
    f1_1_idx = -1
    for idx, fam in enumerate(response.data):  # type: ignore
        if fam["family_id"] == "f1.1":
            f1_1_idx = idx
            break
    family = response.data[f1_1_idx]  # type: ignore
    assert family["family_id"] == "f1.1"
    assert family["family_type"] == "other"
    assert family["person_ids"] == ["mom1", "dad1", "p1", "s1"]
    assert len(family["members"]) == 4
    assert family["members"][2] == {
        "person_id": "p1",
        "family_id": "f1.1",
        "dad_id": "dad1",
        "mom_id": "mom1",
        "sample_id": "p1",
        "member_index": 2,
        "sex": str(Sex.female),
        "role": str(Role.prb),
        "status": str(Status.affected),
        "layout": ANY,  # FIXME temporary handle field variying between two values
        "generated": False,
        "family_bin": None,
        "not_sequenced": False,
        "missing": False,
    }
