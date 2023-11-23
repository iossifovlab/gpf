# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Type, cast
import json

from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import Group
from django.test.client import Client

from users_api.models import WdaeUser


def test_admin_can_get_default_users(admin_client: Client) -> None:
    url = "/api/v3/users"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK


def test_admin_sees_all_default_users(admin_client: Client) -> None:
    url = "/api/v3/users"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2  # admin and user


def test_all_users_have_groups(admin_client: Client) -> None:
    url = "/api/v3/users"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK

    users = response.json()
    assert len(users) > 0
    for user in users:
        assert "groups" in user


def test_users_cant_get_all_users(user_client: Client) -> None:
    url = "/api/v3/users"
    response = user_client.get(url)

    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_unauthenticated_cant_get_all_users(db: None, client: Client) -> None:
    url = "/api/v3/users"
    response = client.get(url)

    # assert response.status_code is status.HTTP_401_UNAUTHORIZED
    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }


def test_admin_can_create_new_users(
    admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    url = "/api/v3/users"
    data = {
        "email": "new@new.com",
    }
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email="new@new.com") is not None


def test_new_user_name_can_be_blank(
    admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    url = "/api/v3/users"
    data = {"email": "new@new.com", "name": ""}
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email="new@new.com") is not None


def test_admin_can_create_new_user_with_groups(
    admin_client: Client, user_model: Type[WdaeUser], empty_group: Group
) -> None:
    url = "/api/v3/users"
    data = {"email": "new@new.com", "groups": [empty_group.name]}
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email="new@new.com") is not None

    user = user_model.objects.get(email="new@new.com")
    assert user.groups.filter(pk=empty_group.id).exists()


def test_admin_can_see_newly_created_user(admin_client: Client) -> None:
    url = "/api/v3/users"

    old_users = admin_client.get(url).json()

    data = {
        "email": "new@new.com",
    }
    admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    new_users = admin_client.get(url).json()
    assert len(new_users) == len(old_users) + 1


def test_new_user_is_not_active(admin_client: Client) -> None:
    url = "/api/v3/users"

    old_users = admin_client.get(url).json()

    data = {
        "email": "new@new.com",
    }
    admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    new_users = admin_client.get(url).json()
    assert len(new_users) == len(old_users) + 1

    new_user = next(
        filter(lambda u: u["email"] == data["email"], new_users), None
    )
    assert new_user is not None
    assert not new_user["hasPassword"]


def test_admin_can_partial_update_user(
    admin_client: Client, active_user: WdaeUser
) -> None:
    url = f"/api/v3/users/{active_user.pk}"
    data = {"name": "Ivan"}

    response = admin_client.patch(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    active_user.refresh_from_db()
    assert active_user.name == "Ivan"


def test_admin_cant_partial_update_user_email(
    admin_client: Client, active_user: WdaeUser
) -> None:
    url = f"/api/v3/users/{active_user.pk}"
    data = {"email": "test@test.com"}

    assert active_user.email != data["email"]
    old_email = active_user.email

    response = admin_client.patch(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code is status.HTTP_400_BAD_REQUEST

    active_user.refresh_from_db()
    assert active_user.email == old_email


def test_user_name_can_be_updated_to_blank(
    admin_client: Client, active_user: WdaeUser
) -> None:
    url = f"/api/v3/users/{active_user.id}"
    data = {
        "id": active_user.id,
        "name": "",
        "groups": [group.name for group in active_user.groups.all()],
    }
    print(data["groups"])

    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    active_user.refresh_from_db()
    assert active_user.name == ""


def test_admin_can_add_user_group(
    admin_client: Client, active_user: WdaeUser,
    empty_group: Group
) -> None:
    user = active_user

    url = f"/api/v3/users/{user.pk}"
    data = {"groups": [empty_group.name]}

    assert not user.groups.filter(name=empty_group.name).exists()
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert user.groups.filter(name=empty_group.name).exists()


def test_admin_can_update_with_new_group(
    admin_client: Client, active_user: WdaeUser
) -> None:
    group_name = "new group"
    user = active_user

    url = f"/api/v3/users/{user.pk}"
    data = {"groups": [group_name]}

    assert not Group.objects.filter(name=group_name).exists()
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert Group.objects.filter(name=group_name).exists()
    assert user.groups.filter(name=group_name).exists()


def test_admin_can_remove_user_group(
    admin_client: Client, empty_group: Group, active_user: WdaeUser
) -> None:
    active_user.groups.add(empty_group)

    url = f"/api/v3/users/{active_user.pk}"
    data = {
        "groups": [
            group.name
            for group in active_user.groups.exclude(id=empty_group.id).all()
        ]
    }
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_200_OK

    active_user.refresh_from_db()
    assert not active_user.groups.filter(id=empty_group.id).exists()


def test_single_admin_cant_remove_superuser_group_from_self(
    admin: WdaeUser, admin_client: Client
) -> None:
    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    admin.groups.add(admin_group)

    url = f"/api/v3/users/{admin.pk}"
    data = {
        "groups": [
            group.name
            for group in admin.groups.exclude(
                name=WdaeUser.SUPERUSER_GROUP
            ).all()
        ]
    }
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is not status.HTTP_200_OK

    admin.refresh_from_db()
    assert admin.groups.filter(name=WdaeUser.SUPERUSER_GROUP).exists()


def test_two_admins_can_not_remove_superuser_group_from_self(
    admin: WdaeUser, admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    other_superuser = user_model.objects.create_superuser(
        "other_admin@test.com", "supersecret"
    )
    other_superuser.groups.add(
        Group.objects.get(name=WdaeUser.SUPERUSER_GROUP)
    )

    url = f"/api/v3/users/{admin.pk}"
    data = {
        "groups": [
            group.name
            for group in admin.groups.exclude(
                name=WdaeUser.SUPERUSER_GROUP
            ).all()
        ]
    }

    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_400_BAD_REQUEST
    admin.refresh_from_db()
    assert admin.groups.filter(name=WdaeUser.SUPERUSER_GROUP).exists()


def test_two_admins_can_remove_superuser_group_from_other(
    admin: WdaeUser, admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    other_superuser = user_model.objects.create_superuser(
        "other_admin@test.com", "supersecret"
    )

    url = f"/api/v3/users/{other_superuser.pk}"
    data = {
        "groups": [
            group.name
            for group in other_superuser.groups.exclude(
                name=WdaeUser.SUPERUSER_GROUP
            ).all()
        ]
    }
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_200_OK

    other_superuser.refresh_from_db()
    assert not other_superuser.groups.filter(
        name=WdaeUser.SUPERUSER_GROUP
    ).exists()


def test_admin_can_delete_user(
    admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    user = user_model.objects.create(email="test@test.com")
    user_id = user.pk
    assert user_model.objects.filter(pk=user_id).exists()

    url = f"/api/v3/users/{user_id}"
    response = admin_client.delete(url)

    assert response.status_code is status.HTTP_204_NO_CONTENT
    assert not user_model.objects.filter(pk=user_id).exists()


def test_admin_can_reset_user_password(
    admin_client: Client, active_user: WdaeUser
) -> None:
    assert active_user.is_active

    url = "/api/v3/users/forgotten_password"
    data = {"email": active_user.email}
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code is status.HTTP_200_OK

    active_user.refresh_from_db()
    assert active_user.has_usable_password()
    assert active_user.is_active


def test_resetting_user_password_does_not_deauthenticates_them(
    admin_client: Client, logged_in_user: tuple[WdaeUser, APIClient]
) -> None:

    user, user_client = logged_in_user
    url = "/api/v3/users/get_user_info"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["loggedIn"]

    reset_password_url = "/api/v3/users/forgotten_password"
    data = {"email": user.email}
    response = admin_client.post(
        reset_password_url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK

    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["loggedIn"]


def test_searching_by_email_finds_only_single_user(
    admin_client: Client, active_user: WdaeUser, user_model: Type[WdaeUser]
) -> None:
    assert user_model.objects.count() > 1

    url = "/api/v3/users"
    params = {"search": active_user.email}
    response = admin_client.get(url, params, format="json")

    assert response.status_code is status.HTTP_200_OK
    assert len(response.json()) == 1


def test_searching_by_username(
    admin_client: Client, active_user: WdaeUser
) -> None:
    active_user.name = "Testy Mc Testington"
    active_user.save()

    url = "/api/v3/users"
    params = {"search": "test"}
    response = admin_client.get(url, params, format="json")
    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == active_user.id


def test_searching_by_email(
    admin_client: Client, active_user: WdaeUser
) -> None:
    url = "/api/v3/users"
    params = {"search": active_user.email[:8]}
    response = admin_client.get(url, params, format="json")
    assert response is not None

    assert response.status_code is status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == active_user.id


def test_user_create_email_case_insensitive(
    admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    url = "/api/v3/users"
    data = {
        "id": 0,
        "email": "ExAmPlE1@iossifovlab.com",
        "name": "Example User",
        "hasPassword": False,
        "groups": ["test_group", "SSC_TEST_GROUP"]
    }
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code is status.HTTP_201_CREATED
    user = user_model.objects.get(email="example1@iossifovlab.com")
    assert user is not None


def test_user_create_email_case_insensitive_with_groups(
    admin_client: Client, user_model: Type[WdaeUser]
) -> None:
    url = "/api/v3/users"
    data = {
        "id": 0,
        "email": "ExAmPlE1@iossifovlab.com",
        "name": "Example User",
        "hasPassword": False,
        "groups": ["test_group", "SSC_TEST_GROUP"]
    }
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code is status.HTTP_201_CREATED
    user = user_model.objects.get(email="example1@iossifovlab.com")
    assert user is not None


def test_user_create_update_case_sensitive_groups(
        admin_client: Client, user_model: Type[WdaeUser]) -> None:

    url = "/api/v3/users"

    data = {
        "id": 0,
        "email": "user1@iossifovlab.com",
        "name": "Example User1",
        "hasPassword": False,
        "groups": ["test_group", "Test_GrouP", "tEsT_gRoUp"]
    }
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_201_CREATED
    user = user_model.objects.get(email="user1@iossifovlab.com")

    assert user is not None
    data = response.json()

    groups = cast(dict, data["groups"])
    print(groups)

    assert "test_group" in groups
    assert "Test_GrouP" in groups
    assert "tEsT_gRoUp" in groups

    url = f"/api/v3/users/{user.pk}"
    data = {"groups": [
        "test_group", "Test_GrouP",
        "any_user", "user1@iossifovlab.com"
    ]}

    response = admin_client.patch(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code is status.HTTP_200_OK

    data = response.json()
    groups = cast(dict, data["groups"])
    print(groups)

    assert "test_group" in groups
    assert "Test_GrouP" in groups
    assert "tEsT_gRoUp" not in groups


def test_admin_cannot_delete_own_user(
    admin_client: Client, admin: WdaeUser, user_model: Type[WdaeUser]
) -> None:
    url = f"/api/v3/users/{admin.id}"
    response = admin_client.delete(url)
    assert response.status_code is status.HTTP_400_BAD_REQUEST
    assert user_model.objects.filter(pk=admin.id).exists()
