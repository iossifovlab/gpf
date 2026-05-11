# pylint: disable=W0621,C0114,C0116,W0212,W0613
from users_api.models import WdaeUser


def test_user_is_inactive_when_password_is_set_to_none(user: WdaeUser) -> None:
    user.set_password(None)
    user.save()

    user.refresh_from_db()

    assert not user.is_active


def test_user_is_active_not_changed_when_password_is_reset(
    user: WdaeUser,
) -> None:
    state_active = user.is_active
    user.reset_password()

    user.refresh_from_db()
    assert state_active == user.is_active
