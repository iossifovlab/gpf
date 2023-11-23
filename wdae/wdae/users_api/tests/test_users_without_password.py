# pylint: disable=W0621,C0114,C0116,W0212,W0613

from users_api.models import WdaeUser


def test_is_inactive_when_newly_created(
    user_without_password: WdaeUser
) -> None:
    assert not user_without_password.is_active


def test_is_inactive_when_password_is_set_to_none(
    user_without_password: WdaeUser
) -> None:
    user_without_password.set_password(None)
    user_without_password.save()

    user_without_password.refresh_from_db()

    assert not user_without_password.is_active


def test_is_active_when_password_is_set(
    user_without_password: WdaeUser
) -> None:
    user_without_password.set_password("alabala")
    user_without_password.save()

    user_without_password.refresh_from_db()

    assert user_without_password.is_active


def test_is_inactive_when_password_is_reset(
    user_without_password: WdaeUser
) -> None:
    user_without_password.reset_password()

    user_without_password.refresh_from_db()

    assert not user_without_password.is_active
