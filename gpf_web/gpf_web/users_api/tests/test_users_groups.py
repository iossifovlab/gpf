# pylint: disable=W0621,C0114,C0116,W0212,W0613

from django.contrib.auth.models import Group

from users_api.models import WdaeUser


def test_without_admin_group_does_not_have_is_staff(user: WdaeUser) -> None:
    assert not user.is_staff


def test_adding_admin_group_sets_is_staff(
    user: WdaeUser, admin_group: Group,
) -> None:
    user.groups.add(admin_group)

    assert user.is_staff


def test_removing_admin_group_unsets_is_staff(
    user: WdaeUser, admin_group: Group,
) -> None:
    user.groups.add(admin_group)

    user.groups.remove(admin_group)
    assert not user.is_staff


def test_deleting_some_group_does_not_break_is_staff(
    user: WdaeUser, admin_group: Group,
) -> None:
    group = Group.objects.create(name="Some Other Group1")

    assert not user.is_staff
    user.groups.add(admin_group)
    assert user.is_staff

    group.delete()
    assert user.is_staff


def test_deleting_admin_group_unsets_is_staff(
    user: WdaeUser, admin_group: Group,
) -> None:
    user.groups.add(admin_group)
    admin_group.delete()

    user.refresh_from_db()
    assert not user.groups.filter(name=WdaeUser.SUPERUSER_GROUP).exists()
    assert not user.is_staff


def test_adding_through_admin_group_sets_is_staff(
    user: WdaeUser, admin_group: Group,
) -> None:
    admin_group.user_set.add(user)

    user.refresh_from_db()

    assert user.is_staff


def test_adding_multiple_users_through_admin_group_sets_is_staff(
    user: WdaeUser, admin_group: Group,
) -> None:
    other_user = WdaeUser.objects.create(email="email@test.com")
    admin_group.user_set.add(user, other_user)

    user.refresh_from_db()
    other_user.refresh_from_db()

    assert user.is_staff
    assert other_user.is_staff
