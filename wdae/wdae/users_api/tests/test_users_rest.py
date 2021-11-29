import json

from rest_framework import status

from django.contrib.auth.models import Group

from users_api.models import WdaeUser


def test_admin_can_get_default_users(admin_client):
    url = "/api/v3/users"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK


def test_admin_sees_all_default_users(admin_client):
    url = "/api/v3/users"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 2  # dev admin, dev staff


def test_all_users_have_groups(admin_client):
    url = "/api/v3/users"
    response = admin_client.get(url)

    assert response.status_code is status.HTTP_200_OK

    users = response.data
    assert len(users) > 0
    for user in users:
        assert "groups" in user


def test_users_cant_get_all_users(user_client):
    url = "/api/v3/users"
    response = user_client.get(url)

    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_unauthenticated_cant_get_all_users(client):
    url = "/api/v3/users"
    response = client.get(url)

    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_admin_can_create_new_users(admin_client, user_model):
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


def test_new_user_name_can_be_blank(admin_client, user_model):
    url = "/api/v3/users"
    data = {"email": "new@new.com", "name": ""}
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email="new@new.com") is not None


def test_admin_can_create_new_user_with_groups(
    admin_client, user_model, empty_group
):
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


def test_admin_can_see_newly_created_user(admin_client):
    url = "/api/v3/users"

    old_users = admin_client.get(url).data

    data = {
        "email": "new@new.com",
    }
    admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    new_users = admin_client.get(url).data
    assert len(new_users) == len(old_users) + 1


def test_new_user_is_not_active(admin_client):
    url = "/api/v3/users"

    old_users = admin_client.get(url).data

    data = {
        "email": "new@new.com",
    }
    admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    new_users = admin_client.get(url).data
    assert len(new_users) == len(old_users) + 1

    new_user = next(
        filter(lambda u: u["email"] == data["email"], new_users), None
    )
    assert not new_user["hasPassword"]


def test_admin_can_partial_update_user(admin_client, user_model):
    user = user_model.objects.first()

    url = "/api/v3/users/{}".format(user.pk)
    data = {"name": "Ivan"}

    response = admin_client.patch(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert user.name == "Ivan"


def test_admin_cant_partial_update_user_email(admin_client, user_model):
    user = user_model.objects.first()

    url = "/api/v3/users/{}".format(user.pk)
    data = {"email": "test@test.com"}

    assert user.email != data["email"]
    old_email = user.email

    response = admin_client.patch(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code is status.HTTP_400_BAD_REQUEST

    user.refresh_from_db()
    assert user.email == old_email


def test_user_name_can_be_updated_to_blank(admin_client, active_user):
    url = "/api/v3/users/{}".format(active_user.id)
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


def test_admin_can_add_user_group(admin_client, active_user, empty_group):
    user = active_user

    url = "/api/v3/users/{}".format(user.pk)
    data = {"groups": [empty_group.name]}
    data["groups"] += [g.name for g in user.protected_groups]

    assert not user.groups.filter(name=empty_group.name).exists()
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert user.groups.filter(name=empty_group.name).exists()


def test_admin_can_update_with_new_group(admin_client, active_user):
    group_name = "new group"
    user = active_user

    url = "/api/v3/users/{}".format(user.pk)
    data = {"groups": [group_name]}
    data["groups"] += [g.name for g in user.protected_groups]

    assert not Group.objects.filter(name=group_name).exists()
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert Group.objects.filter(name=group_name).exists()
    assert user.groups.filter(name=group_name).exists()


def test_admin_can_remove_user_group(admin_client, empty_group, active_user):
    active_user.groups.add(empty_group)

    url = "/api/v3/users/{}".format(active_user.pk)
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
    admin, admin_client
):
    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    admin.groups.add(admin_group)

    url = "/api/v3/users/{}".format(admin.pk)
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
    admin, admin_client, user_model
):
    other_superuser = user_model.objects.create_superuser(
        "other_admin@test.com", "supersecret"
    )
    other_superuser.groups.add(
        Group.objects.get(name=WdaeUser.SUPERUSER_GROUP)
    )

    url = "/api/v3/users/{}".format(admin.pk)
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
    admin, admin_client, user_model
):
    other_superuser = user_model.objects.create_superuser(
        "other_admin@test.com", "supersecret"
    )

    url = "/api/v3/users/{}".format(other_superuser.pk)
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


def test_protected_groups_cant_be_removed(
    admin_client, empty_group, active_user
):
    url = "/api/v3/users/{}".format(active_user.pk)
    data = {"groups": [empty_group.name]}
    response = admin_client.put(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_400_BAD_REQUEST

    assert active_user.protected_groups.count() == 2
    assert not active_user.groups.filter(id=empty_group.id).exists()


def test_admin_can_delete_user(admin_client, user_model):
    user = user_model.objects.create(email="test@test.com")
    user_id = user.pk
    assert user_model.objects.filter(pk=user_id).exists()

    url = "/api/v3/users/{}".format(user_id)
    response = admin_client.delete(url)

    assert response.status_code is status.HTTP_204_NO_CONTENT
    assert not user_model.objects.filter(pk=user_id).exists()


def test_admin_can_reset_user_password(admin_client, active_user):
    assert active_user.is_active

    url = "/api/v3/users/{}/password_reset".format(active_user.pk)
    response = admin_client.post(url)
    assert response.status_code is status.HTTP_204_NO_CONTENT

    active_user.refresh_from_db()
    assert active_user.has_usable_password()
    assert active_user.is_active


def test_resetting_user_password_does_not_deauthenticates_them(
        admin_client, logged_in_user):

    user, user_client = logged_in_user
    url = "/api/v3/users/get_user_info"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["loggedIn"]

    reset_password_url = "/api/v3/users/{}/password_reset".format(user.pk)

    response = admin_client.post(reset_password_url)
    assert response.status_code is status.HTTP_204_NO_CONTENT

    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["loggedIn"]


def test_user_cant_reset_other_user_password(user_client, active_user):
    assert active_user.has_usable_password()

    url = "/api/v3/users/{}/password_reset".format(active_user.pk)
    response = user_client.post(url)

    assert response.status_code is status.HTTP_403_FORBIDDEN

    active_user.refresh_from_db()
    assert active_user.has_usable_password()
    assert active_user.is_active


def test_searching_by_email_finds_only_single_user(
    admin_client, active_user, user_model
):
    assert user_model.objects.count() > 1

    url = "/api/v3/users"
    params = {"search": active_user.email}
    response = admin_client.get(url, params, format="json")

    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 1


def test_searching_by_any_user_finds_all_users(
    admin_client, active_user, user_model
):
    users_count = user_model.objects.count()
    assert users_count > 1

    url = "/api/v3/users"
    params = {"search": "any_user"}
    response = admin_client.get(url, params, format="json")

    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == users_count


def test_searching_by_username(admin_client, active_user):
    active_user.name = "Testy Mc Testington"
    active_user.save()

    url = "/api/v3/users"
    params = {"search": "test"}
    response = admin_client.get(url, params, format="json")
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == active_user.id


def test_searching_by_email(admin_client, active_user):
    url = "/api/v3/users"
    params = {"search": active_user.email[:8]}
    response = admin_client.get(url, params, format="json")
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == active_user.id


def test_user_create_email_case_insensitive(admin_client, user_model):
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

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    user = user_model.objects.get(email="example1@iossifovlab.com")

    assert user is not None
    print(response.data)
    data = response.data
    groups = data["groups"]
    print(groups)

    assert "example1@iossifovlab.com" in groups
    assert "ExAmPlE1@iossifovlab.com" not in groups


def test_user_create_email_case_insensitive_with_groups(
        admin_client, user_model):

    url = "/api/v3/users"

    data = {
        "id": 0,
        "email": "ExAmPlE1@iossifovlab.com",
        "name": "Example User",
        "hasPassword": False,
        "groups": ["test_group", "ExAmPlE1@iossifovlab.com", "SSC_TEST_GROUP"]
    }
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    user = user_model.objects.get(email="example1@iossifovlab.com")

    assert user is not None
    print(response.data)
    data = response.data
    groups = data["groups"]
    print(groups)

    assert "example1@iossifovlab.com" in groups
    assert "ExAmPlE1@iossifovlab.com" not in groups


def test_user_create_update_case_sensitive_groups(
        admin_client, user_model):

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
    print(response.data)
    data = response.data
    groups = data["groups"]
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
    print(response)
    print(response.data)
    assert response.status_code is status.HTTP_200_OK

    print(response.data)
    groups = response.data["groups"]
    print(groups)

    assert "test_group" in groups
    assert "Test_GrouP" in groups
    assert "tEsT_gRoUp" not in groups


def test_admin_cannot_delete_own_user(admin_client, admin, user_model):
    url = f"/api/v3/users/{admin.id}"
    response = admin_client.delete(url)
    assert response.status_code is status.HTTP_400_BAD_REQUEST
    assert user_model.objects.filter(pk=admin.id).exists()
