# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import cast

import pytest
from datasets_api.models import Dataset
from datasets_api.permissions import user_has_permission
from django.contrib.auth.models import Group, User
from django.test.client import Client
from rest_framework import status
from users_api.models import WdaeUser


def test_admin_can_get_groups(admin_client: Client) -> None:
    url = "/api/v3/groups"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert len(response.json()) > 0


def test_user_cant_see_groups(user_client: Client) -> None:
    url = "/api/v3/groups"
    response = user_client.get(url)

    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_groups_have_ids_and_names(admin_client: Client) -> None:
    url = "/api/v3/groups"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    for group in data:
        assert "id" in group
        assert "name" in group


def test_groups_have_users_and_datasets(admin_client: Client) -> None:
    url = "/api/v3/groups"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    for group in data:
        assert "users" in group
        assert "datasets" in group


def test_single_group_has_users_and_datasets(admin_client: Client) -> None:
    groups = Group.objects.all()
    for group in groups:
        url = f"/api/v3/groups/{group.name}"
        response = admin_client.get(url)

        assert response.status_code is status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "datasets" in data


def test_admin_cant_delete_groups(admin_client: Client) -> None:
    all_groups = Group.objects.all()
    assert len(all_groups) > 0

    for group in all_groups:
        url = f"/api/v3/groups/{group.pk}"
        del_response = admin_client.delete(
            url, content_type="application/json", format="json",
        )

        assert del_response.status_code is status.HTTP_405_METHOD_NOT_ALLOWED

    url = "/api/v3/groups"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK

    assert len(response.json()) is len(all_groups)


def test_admin_can_create_groups(admin_client: Client) -> None:
    new_group_name = "NewAwesomeGroup"
    data = {"name": new_group_name}

    assert not Group.objects.all().filter(name=new_group_name).exists()

    url = "/api/v3/groups"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code is status.HTTP_201_CREATED
    assert Group.objects.all().filter(name=new_group_name).exists()


def test_user_cant_create_groups(user_client: Client) -> None:
    new_group_name = "NewAwesomeGroup"
    data = {"name": new_group_name}

    assert not Group.objects.all().filter(name=new_group_name).exists()

    url = "/api/v3/groups"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code is status.HTTP_403_FORBIDDEN
    assert not Group.objects.all().filter(name=new_group_name).exists()


def test_admin_can_rename_groups(
    admin_client: Client,
    group_with_user: tuple[Group, WdaeUser],
) -> None:
    group, _ = group_with_user
    assert group is not None

    test_name = "AwesomeGroup"
    assert group.name is not test_name

    url = f"/api/v3/groups/{group.name}"

    data = {"id": group.id, "name": test_name}

    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert data["name"] == test_name

    group.refresh_from_db()
    assert group.name == test_name


def test_group_has_all_users(admin_client: Client, group: Group) -> None:
    test_emails = ["test@email.com", "other@email.com", "last@example.com"]
    for email in test_emails:
        group.user_set.create(email=email)  # type: ignore

    url = f"/api/v3/groups/{group.name}"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    for email in test_emails:
        assert email in data["users"]


def test_no_empty_groups_are_accessible(admin_client: Client) -> None:
    groups_count = Group.objects.all().count()
    new_group = Group.objects.create(name="New Group")

    url = "/api/v3/groups"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.json()) == groups_count

    url = f"/api/v3/groups/{new_group.id}"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_404_NOT_FOUND


def test_empty_group_with_permissions_is_shown(
    admin_client: Client, dataset: Dataset,
) -> None:
    group = Group.objects.create(name="New Group")

    dataset.groups.add(group)

    url = "/api/v3/groups"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data) == 25
    new_group_reponse = next(
        (
            response_group
            for response_group in data
            if response_group["name"] == group.name
        ),
        None,
    )
    assert new_group_reponse
    assert new_group_reponse["datasets"][0]["datasetId"] == dataset.dataset_id


def test_group_has_all_datasets(
    admin_client: Client,
    group_with_user: tuple[Group, WdaeUser],
    dataset: Dataset,
) -> None:
    group, _ = group_with_user

    url = f"/api/v3/groups/{group.name}"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data["datasets"]) == 0

    dataset.groups.add(group)

    url = f"/api/v3/groups/{group.name}"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data["datasets"]) == 1
    assert data["datasets"][0]["datasetId"] == dataset.dataset_id
    assert data["datasets"][0]["datasetName"] == "Dataset1"
    assert data["datasets"][0]["broken"] is False


def test_grant_permission_for_group(
    admin_client: Client, group_with_user: tuple[Group, WdaeUser],
    dataset: Dataset,
) -> None:
    group, wdae_user = group_with_user
    user = cast(User, wdae_user)
    data = {"datasetId": dataset.dataset_id, "groupName": group.name}

    assert not user_has_permission("test_data", user, dataset.dataset_id)

    url = "/api/v3/groups/grant-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert user_has_permission("test_data", user, dataset.dataset_id)


def test_grant_permission_creates_new_group(
    admin_client: Client, user: WdaeUser, dataset: Dataset,
) -> None:
    group_name = "NewGroup"
    data = {"datasetId": dataset.dataset_id, "groupName": group_name}

    assert not user_has_permission(
        "test_data", cast(User, user), dataset.dataset_id,
    )

    url = "/api/v3/groups/grant-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert Group.objects.filter(name=group_name).count() == 1


def test_grant_permission_creates_new_group_case_sensitive(
    admin_client: Client, user: WdaeUser, dataset: Dataset,
) -> None:

    group_name = "group_name_P"
    data = {"datasetId": dataset.dataset_id, "groupName": group_name}

    assert not user_has_permission(
        "test_data", cast(User, user), dataset.dataset_id,
    )

    url = "/api/v3/groups/grant-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert Group.objects.filter(name=group_name).count() == 1
    assert Group.objects.filter(name=group_name.lower()).count() == 0


def test_not_admin_cant_grant_permissions(
    user_client: Client, group_with_user: tuple[Group, WdaeUser],
    dataset: Dataset,
) -> None:
    group, wdae_user = group_with_user
    user = cast(User, wdae_user)

    data = {"datasetId": dataset.dataset_id, "groupName": group.name}

    assert not user_has_permission("test_data", user, dataset.dataset_id)

    url = "/api/v3/groups/grant-permission"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not user_has_permission("test_data", user, dataset.dataset_id)


def test_not_admin_grant_permissions_does_not_create_group(
    user_client: Client, dataset: Dataset,
) -> None:
    group_name = "NewGroup"
    data = {"datasetId": dataset.dataset_id, "groupName": group_name}

    url = "/api/v3/groups/grant-permission"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Group.objects.filter(name=group_name).count() == 0


def test_revoke_permission_for_group(
    admin_client: Client, group_with_user: tuple[Group, WdaeUser],
    dataset: Dataset,
) -> None:
    group, wdae_user = group_with_user
    user = cast(User, wdae_user)

    data = {"datasetId": dataset.dataset_id, "groupId": group.id}

    dataset.groups.add(group)

    assert user_has_permission("test_data", user, dataset.dataset_id)

    url = "/api/v3/groups/revoke-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert not user_has_permission("test_data", user, dataset.dataset_id)


def test_not_admin_cant_revoke_permissions(
    user_client: Client, group_with_user: tuple[Group, WdaeUser],
    dataset: Dataset,
) -> None:
    group, wdae_user = group_with_user
    user = cast(User, wdae_user)

    data = {"datasetId": dataset.dataset_id, "groupId": group.id}
    dataset.groups.add(group)

    assert user_has_permission("test_data", user, dataset.dataset_id)

    url = "/api/v3/groups/revoke-permission"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert user_has_permission("test_data", user, dataset.dataset_id)


def test_cant_revoke_default_permissions(
    user_client: Client, dataset: Dataset,
) -> None:
    Dataset.recreate_dataset_perm(dataset.dataset_id)

    url = "/api/v3/groups/revoke-permission"

    assert len(dataset.default_groups) > 0

    for group_name in dataset.default_groups:
        group = Group.objects.get(name=group_name)
        data = {"datasetId": dataset.dataset_id, "groupId": group.id}

        response = user_client.post(
            url,
            json.dumps(data),
            content_type="application/json",
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert dataset.groups.filter(pk=group.pk).exists()


@pytest.mark.parametrize(
    "page,status_code,length, first_name, last_name",
    [
        (1, status.HTTP_200_OK, 25, "Dataset1", "Group27"),
        (2, status.HTTP_200_OK, 25, "Group28", "Group5"),
        (3, status.HTTP_200_OK, 25, "Group50", "Group72"),
        (4, status.HTTP_200_OK, 25, "Group73", "Group95"),
        (5, status.HTTP_200_OK, 25, "Group96", None),
        (7, status.HTTP_204_NO_CONTENT, None, None, None),
    ],
)
def test_groups_pagination(
        admin_client: Client, hundred_groups: list[Group], page: int,
        status_code: int, length: int | None,
        first_name: str | None, last_name: str | None,
) -> None:
    url = f"/api/v3/groups?page={page}"
    response = admin_client.get(url)
    assert response.status_code == status_code
    if response.status_code == status.HTTP_204_NO_CONTENT:
        return

    data = response.json()

    if length is not None:
        assert len(data) == length

    if first_name is not None:
        assert data[0]["name"] == first_name

    if last_name is not None:
        assert length is not None
        assert data[length - 1]["name"] == last_name


def test_groups_search(
    admin_client: Client, hundred_groups: list[Group],
) -> None:
    url = "/api/v3/groups?search=Group1"
    response = admin_client.get(url)
    assert len(response.json()) == 12


@pytest.mark.parametrize(
    "page,status_code,length",
    [
        (1, status.HTTP_200_OK, 25),
        (2, status.HTTP_200_OK, 25),
        (3, status.HTTP_200_OK, 25),
        (4, status.HTTP_200_OK, 25),
        (5, status.HTTP_200_OK, 3),
        (6, status.HTTP_204_NO_CONTENT, None),
    ],
)
def test_groups_search_pagination(
    admin_client: Client,
    hundred_groups: list[Group],
    page: int, status_code: int, length: int | None,
) -> None:
    url = f"/api/v3/groups?page={page}&search=Group"
    response = admin_client.get(url)
    assert response.status_code == status_code
    if response.status_code == status.HTTP_204_NO_CONTENT:
        return

    data = response.json()
    if length is not None:
        assert len(data) == length


def test_user_group_routes(admin_client: Client, user: WdaeUser) -> None:
    assert not user.groups.filter(name="Test group").exists()

    group = Group.objects.create(name="Test group")
    data = {"userEmail": user.email, "groupName": group.name}

    url = "/api/v3/groups/add-user"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert user.groups.filter(name="Test group").exists()

    url = "/api/v3/groups/remove-user"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not user.groups.filter(name="Test group").exists()


def test_group_retrieve(
    admin_client: Client, hundred_groups: list[Group],
) -> None:
    url = "/api/v3/groups/Group1"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["name"] == "Group1"
    assert data["users"] == ["user@example.com"]
    assert data["datasets"] == [{
        "datasetName": "Dataset1",
        "datasetId": "Dataset1",
        "broken": False,
    }]


def test_group_retrieve_alphabetical_order(
    admin_client: Client, hundred_groups: list[Group],
) -> None:
    url = "/api/v3/groups/any_dataset"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["name"] == "any_dataset"
    assert data["users"] == []
    assert data["datasets"][0]["datasetName"] == "(TEST_REMOTE) iossifov_2014"
    assert data["datasets"][1]["datasetName"] == "comp"
    assert data["datasets"][3]["datasetName"] == "Dataset1"
    assert data["datasets"][3]["datasetName"] == "Dataset1"
    assert data["datasets"][7]["datasetName"] == "f1_group"
    assert data["datasets"][8]["datasetName"] == "f1_study"
    assert data["datasets"][9]["datasetName"] == "f1_trio"
    assert data["datasets"][14]["datasetName"] == "FAKE_STUDY"
    assert data["datasets"][-1]["datasetName"] == "TRIO"


def test_group_retrieve_missing(admin_client: Client) -> None:
    url = "/api/v3/groups/somegroupthatdoesnotexist"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
