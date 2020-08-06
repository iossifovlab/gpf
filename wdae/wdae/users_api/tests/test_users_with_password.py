def test_user_is_inactive_when_password_is_set_to_none(user):
    user.set_password(None)
    user.save()

    user.refresh_from_db()

    assert not user.is_active


def test_user_is_active_not_changed_when_password_is_reset(user):
    state_active = user.is_active
    user.reset_password()

    user.refresh_from_db()
    assert state_active == user.is_active
