# ruff: noqa: ARG001, S106
# pylint: disable=W0621,C0114,C0116,W0212,W0613

import uuid
from datetime import timedelta
from typing import cast

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from oauth2_provider.models import Application, get_access_token_model
from rest_framework.test import APIClient

from users_api.models import WdaeUser


@pytest.fixture
def user_model() -> type[WdaeUser]:
    return cast(type[WdaeUser], get_user_model())  # type: ignore


@pytest.fixture
def empty_group(db: None) -> Group:
    return Group.objects.create(name="Empty group")


@pytest.fixture
def empty_group_2(db: None) -> Group:
    return Group.objects.create(name="Empty group 2")


@pytest.fixture
def active_user(db: None, user_model: type[WdaeUser]) -> WdaeUser:
    user = user_model.objects.create_user(  # type: ignore
        email="new@new.com", password="secret",
    )

    assert user.is_active
    return user


@pytest.fixture
def inactive_user(db: None, user_model: type[WdaeUser]) -> WdaeUser:
    user = user_model.objects.create_user(email="new@new.com")  # type: ignore

    assert not user.is_active
    return user


@pytest.fixture
def logged_in_user(
    active_user: WdaeUser, oauth_app: Application,
) -> tuple[WdaeUser, APIClient]:
    access_token = get_access_token_model()
    user_access_token = access_token(
        user=active_user,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="active-user-token",
        application=oauth_app,
    )
    user_access_token.save()
    client = APIClient(HTTP_AUTHORIZATION="Bearer active-user-token")
    client.login(email=active_user.email, password="secret")
    return active_user, client


@pytest.fixture
def admin_group(user: WdaeUser) -> Group:
    return Group.objects.create(name=WdaeUser.SUPERUSER_GROUP)


@pytest.fixture
def researcher(db: None) -> WdaeUser:
    res = WdaeUser.objects.create_user(email="fake@fake.com")  # type: ignore
    res.name = "fname"
    res.set_password("alabala")
    res.save()

    return res


@pytest.fixture
def researcher_without_password(db: None) -> WdaeUser:
    res = WdaeUser.objects.create_user(email="fake@fake.com")  # type: ignore
    res.name = "fname"
    res.save()

    return res


@pytest.fixture
def unique_test_user(db: None) -> WdaeUser:
    uid = uuid.uuid1()
    res = WdaeUser.objects.create_user(  # type: ignore
        email=f"fake{uid}@unique.com")
    res.name = f"fname{uid}"
    res.set_password("alabala")
    res.save()

    return res
