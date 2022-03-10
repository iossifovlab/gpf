import pytest

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

from users_api.models import WdaeUser


@pytest.fixture()
def user_model():
    return get_user_model()


@pytest.fixture()
def empty_group(db):
    return Group.objects.create(name="Empty group")


@pytest.fixture()
def empty_group_2(db):
    return Group.objects.create(name="Empty group 2")


@pytest.fixture()
def active_user(db, user_model):
    user = user_model.objects.create_user(
        email="new@new.com", password="secret"
    )

    assert user.is_active
    return user


@pytest.fixture()
def inactive_user(db, user_model):
    user = user_model.objects.create_user(email="new@new.com")

    assert not user.is_active
    return user


@pytest.fixture()
def logged_in_user(active_user):
    client = APIClient()
    client.login(email=active_user.email, password="secret")
    return active_user, client


@pytest.fixture()
def three_new_users(db, user_model):
    users = []
    for email_id in range(3):
        user = user_model.objects.create(
            email="user{}@example.com".format(email_id + 1)
        )
        users.append(user)

    return users


@pytest.fixture()
def three_users_in_a_group(db, three_new_users, empty_group):
    empty_group.user_set.add(*three_new_users)
    for user in three_new_users:
        user.refresh_from_db()

    return three_new_users, empty_group


@pytest.fixture()
def three_users_in_groups(db, three_new_users, empty_group, empty_group_2):
    empty_group.user_set.add(*three_new_users)
    empty_group_2.user_set.add(*three_new_users)
    for user in three_new_users:
        user.refresh_from_db()

    return three_new_users, empty_group, empty_group_2


@pytest.fixture()
def admin_group(user):
    admin_group = Group.objects.create(name=WdaeUser.SUPERUSER_GROUP)

    return admin_group


@pytest.fixture()
def researcher(db):
    res = WdaeUser.objects.create_user(email="fake@fake.com")
    res.name = "fname"
    res.email = "fake@fake.com"
    res.set_password("alabala")
    res.save()

    return res


@pytest.fixture()
def researcher_without_password(db):
    res = WdaeUser.objects.create_user(email="fake@fake.com")
    res.name = "fname"
    res.email = "fake@fake.com"
    res.save()

    return res
