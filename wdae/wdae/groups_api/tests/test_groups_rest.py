# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pytest

from django.contrib.auth.models import Group
from rest_framework import status

from datasets_api.models import Dataset
from datasets_api.permissions import user_has_permission


def test_admin_can_get_groups(admin_client):
    url = "/api/v3/groups"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) > 0


def test_user_cant_see_groups(user_client):
    url = "/api/v3/groups"
    response = user_client.get(url)

    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_groups_have_ids_and_names(admin_client):
    url = "/api/v3/groups"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK

    assert len(response.data) > 0
    for group in response.data:
        assert "id" in group
        assert "name" in group


def test_groups_have_users_and_datasets(admin_client):
    url = "/api/v3/groups"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK

    assert len(response.data) > 0
    for group in response.data:
        assert "users" in group
        assert "datasets" in group


def test_single_group_has_users_and_datasets(admin_client):
    groups = Group.objects.all()
    for group in groups:
        url = "/api/v3/groups/{}".format(group.name)
        response = admin_client.get(url)

        assert response.status_code is status.HTTP_200_OK
        assert "users" in response.data
        assert "datasets" in response.data


def test_admin_cant_delete_groups(admin_client):
    all_groups = Group.objects.all()
    assert len(all_groups) > 0

    for group in all_groups:
        url = "/api/v3/groups/{}".format(group.pk)
        del_response = admin_client.delete(
            url, content_type="application/json", format="json"
        )

        assert del_response.status_code is status.HTTP_405_METHOD_NOT_ALLOWED

    url = "/api/v3/groups"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK

    assert len(response.data) is len(all_groups)


def test_admin_can_create_groups(admin_client):
    new_group_name = "NewAwesomeGroup"
    data = {"name": new_group_name}

    assert not Group.objects.all().filter(name=new_group_name).exists()

    url = "/api/v3/groups"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_201_CREATED
    assert Group.objects.all().filter(name=new_group_name).exists()


def test_user_cant_create_groups(user_client):
    new_group_name = "NewAwesomeGroup"
    data = {"name": new_group_name}

    assert not Group.objects.all().filter(name=new_group_name).exists()

    url = "/api/v3/groups"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_403_FORBIDDEN
    assert not Group.objects.all().filter(name=new_group_name).exists()


def test_admin_can_rename_groups(admin_client, group_with_user):
    group, _ = group_with_user
    assert group is not None

    test_name = "AwesomeGroup"
    assert group.name is not test_name

    url = "/api/v3/groups/{}".format(group.name)

    data = {"id": group.id, "name": test_name}

    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK
    assert response.data["name"] == test_name

    group.refresh_from_db()
    assert group.name == test_name


def test_group_has_all_users(admin_client, group):
    test_emails = ["test@email.com", "other@email.com", "last@example.com"]
    for email in test_emails:
        group.user_set.create(email=email)

    url = "/api/v3/groups/{}".format(group.name)
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    for email in test_emails:
        assert email in response.data["users"]


def test_no_empty_groups_are_accessible(admin_client):
    groups_count = Group.objects.all().count()
    new_group = Group.objects.create(name="New Group")

    url = "/api/v3/groups"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == groups_count

    url = "/api/v3/groups/{}".format(new_group.id)
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_404_NOT_FOUND


def test_empty_group_with_permissions_is_shown(admin_client, dataset):
    group = Group.objects.create(name="New Group")

    dataset.groups.add(group)

    url = "/api/v3/groups"
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 25
    new_group_reponse = next(
        (
            response_group
            for response_group in response.data
            if response_group["name"] == group.name
        ),
        None,
    )
    assert new_group_reponse
    assert new_group_reponse["datasets"][0]["datasetId"] == dataset.dataset_id


def test_group_has_all_datasets(admin_client, group_with_user, dataset):
    group, _ = group_with_user

    url = "/api/v3/groups/{}".format(group.name)
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data["datasets"]) == 0

    dataset.groups.add(group)

    url = "/api/v3/groups/{}".format(group.name)
    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data["datasets"]) == 1
    assert response.data["datasets"][0]["datasetId"] == dataset.dataset_id
    assert response.data["datasets"][0]["datasetName"] == "Dataset1"
    assert response.data["datasets"][0]["broken"] is False


def test_grant_permission_for_group(admin_client, group_with_user, dataset):
    group, user = group_with_user
    data = {"datasetId": dataset.dataset_id, "groupName": group.name}

    assert not user_has_permission(user, dataset)

    url = "/api/v3/groups/grant-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert user_has_permission(user, dataset)


def test_grant_permission_creates_new_group(admin_client, user, dataset):
    groupName = "NewGroup"
    data = {"datasetId": dataset.dataset_id, "groupName": groupName}

    assert not user_has_permission(user, dataset)

    url = "/api/v3/groups/grant-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert Group.objects.filter(name=groupName).count() == 1


def test_grant_permission_creates_new_group_case_sensitive(
        admin_client, user, dataset):

    group_name = "group_name_P"
    data = {"datasetId": dataset.dataset_id, "groupName": group_name}

    assert not user_has_permission(user, dataset)

    url = "/api/v3/groups/grant-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert Group.objects.filter(name=group_name).count() == 1
    assert Group.objects.filter(name=group_name.lower()).count() == 0


def test_not_admin_cant_grant_permissions(
    user_client, group_with_user, dataset
):
    group, user = group_with_user
    data = {"datasetId": dataset.dataset_id, "groupName": group.name}

    assert not user_has_permission(user, dataset)

    url = "/api/v3/groups/grant-permission"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not user_has_permission(user, dataset)


def test_not_admin_grant_permissions_does_not_create_group(
    user_client, dataset
):
    groupName = "NewGroup"
    data = {"datasetId": dataset.dataset_id, "groupName": groupName}

    url = "/api/v3/groups/grant-permission"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Group.objects.filter(name=groupName).count() == 0


def test_revoke_permission_for_group(admin_client, group_with_user, dataset):
    group, user = group_with_user
    data = {"datasetId": dataset.dataset_id, "groupId": group.id}

    dataset.groups.add(group)

    assert user_has_permission(user, dataset)

    url = "/api/v3/groups/revoke-permission"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert not user_has_permission(user, dataset)


def test_not_admin_cant_revoke_permissions(
    user_client, group_with_user, dataset
):
    group, user = group_with_user
    data = {"datasetId": dataset.dataset_id, "groupId": group.id}
    dataset.groups.add(group)

    assert user_has_permission(user, dataset)

    url = "/api/v3/groups/revoke-permission"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert user_has_permission(user, dataset)


def test_cant_revoke_default_permissions(user_client, dataset):
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
    ]
)
def test_groups_pagination(
        admin_client, hundred_groups, page,
        status_code, length, first_name, last_name
):
    url = f"/api/v3/groups?page={page}"
    response = admin_client.get(url)
    assert response.status_code == status_code

    if length is not None:
        assert len(response.data) == length

    if first_name is not None:
        assert response.data[0]["name"] == first_name

    if last_name is not None:
        assert response.data[length - 1]["name"] == last_name


def test_groups_search(admin_client, hundred_groups):
    url = "/api/v3/groups?search=Group1"
    response = admin_client.get(url)
    assert len(response.data) == 12


@pytest.mark.parametrize(
    "page,status_code,length",
    [
        (1, status.HTTP_200_OK, 25),
        (2, status.HTTP_200_OK, 25),
        (3, status.HTTP_200_OK, 25),
        (4, status.HTTP_200_OK, 25),
        (5, status.HTTP_200_OK, 3),
        (6, status.HTTP_204_NO_CONTENT, None),
    ]
)
def test_groups_search_pagination(
        admin_client, hundred_groups, page, status_code, length
):
    url = f"/api/v3/groups?page={page}&search=Group"
    response = admin_client.get(url)
    assert response.status_code == status_code
    if length is not None:
        assert len(response.data) == length


def test_user_group_routes(admin_client, user):
    assert not user.groups.filter(name="Test group").exists()

    group = Group.objects.create(name="Test group")
    data = {"userEmail": user.email, "groupName": group.name}

    url = "/api/v3/groups/add-user"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert user.groups.filter(name="Test group").exists()

    url = "/api/v3/groups/remove-user"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not user.groups.filter(name="Test group").exists()


def test_group_retrieve(admin_client, hundred_groups):
    url = "/api/v3/groups/Group1"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.data

    assert data["name"] == "Group1"
    assert data["users"] == ["user@example.com"]
    assert data["datasets"] == [{
        "datasetName": "Dataset1",
        "datasetId": "Dataset1",
        "broken": False,
    }]


def test_group_retrieve_missing(admin_client):
    url = "/api/v3/groups/somegroupthatdoesnotexist"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
