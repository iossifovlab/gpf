# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from django.test.client import Client
from rest_framework import status


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_list_families_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/t4c8_dataset")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {"f2.1", "f2.3"}  # type: ignore


STUDY_1_ONLY_PERSONS = {"p1", "s1", "p3", "s3"}


TAGS_URL = (
    "/api/v3/families/t4c8_dataset"
    "?tags=tag_nuclear_family,tag_trio_family"
)


@pytest.mark.usefixtures("t4c8_wgpf_instance")
def test_list_families_by_tags_of_the_whole_dataset(
    admin_client: Client,
) -> None:
    response = admin_client.get(TAGS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "f1.1", "f1.3", "f2.1", "f2.3",
    }


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_list_families_by_tags_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get(TAGS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {"f2.1", "f2.3"}  # type: ignore


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_list_all_details_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/t4c8_dataset/all")

    assert response.status_code == status.HTTP_200_OK
    families = response.json()
    assert {fam["family_id"] for fam in families} == {"f2.1", "f2.3"}
    person_ids = {
        member["person_id"]
        for fam in families
        for member in fam["members"]
    }
    assert person_ids & STUDY_1_ONLY_PERSONS == set()


@pytest.mark.parametrize("url", [
    "/api/v3/families/t4c8_dataset/f2.1",
    "/api/v3/families/t4c8_dataset/f2.1/members",
    "/api/v3/families/t4c8_dataset/f2.1/members/all",
    "/api/v3/families/t4c8_dataset/f2.1/members/ch1",
])
@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_family_details_of_allowed_study_under_partial_grant(
    user_client: Client,
    url: str,
) -> None:
    response = user_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("url", [
    "/api/v3/families/t4c8_dataset/f1.1",
    "/api/v3/families/t4c8_dataset/f1.1/members",
    "/api/v3/families/t4c8_dataset/f1.1/members/all",
    "/api/v3/families/t4c8_dataset/f1.1/members/p1",
])
@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_family_details_of_other_study_under_partial_grant_is_404(
    user_client: Client,
    url: str,
) -> None:
    response = user_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_list_members_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/t4c8_dataset/f2.3/members")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "mom3", "dad3", "ch3", "ch4",
    }


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_list_families_under_full_grant(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/t4c8_dataset")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "f1.1", "f1.3", "f2.1", "f2.3",
    }


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_list_all_details_under_full_grant(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/t4c8_dataset/all")

    assert response.status_code == status.HTTP_200_OK
    families = response.json()
    assert {fam["family_id"] for fam in families} == {
        "f1.1", "f1.3", "f2.1", "f2.3",
    }


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
@pytest.mark.parametrize("url", [
    "/api/v3/families/t4c8_dataset/f1.1",
    "/api/v3/families/t4c8_dataset/f1.1/members",
    "/api/v3/families/t4c8_dataset/f1.1/members/all",
    "/api/v3/families/t4c8_dataset/f1.1/members/p1",
])
def test_family_details_of_study_1_under_full_grant(
    user_client: Client,
    url: str,
) -> None:
    response = user_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "p1" in response.content.decode()
