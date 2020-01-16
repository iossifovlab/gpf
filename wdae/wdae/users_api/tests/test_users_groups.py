from users_api.models import WdaeUser
from django.contrib.auth.models import Group


def test_without_admin_group_does_not_have_is_staff(user):
    assert not user.is_staff


def test_adding_admin_group_sets_is_staff(user, admin_group):
    user.groups.add(admin_group)

    assert user.is_staff


def test_removing_admin_group_unsets_is_staff(user, admin_group):
    user.groups.add(admin_group)

    user.groups.remove(admin_group)
    assert not user.is_staff


def test_deleting_some_group_does_not_break_is_staff(user, admin_group):
    group = Group.objects.create(name="Some Other Group1")

    assert not user.is_staff
    user.groups.add(admin_group)
    assert user.is_staff

    group.delete()
    assert user.is_staff


def test_deleting_admin_group_unsets_is_staff(user, admin_group):
    user.groups.add(admin_group)
    admin_group.delete()

    user.refresh_from_db()
    assert not user.groups.filter(name=WdaeUser.SUPERUSER_GROUP)\
        .exists()
    assert not user.is_staff


def test_adding_through_admin_group_sets_is_staff(user, admin_group):
    admin_group.user_set.add(user)

    user.refresh_from_db()

    assert user.is_staff


def test_adding_multiple_users_through_admin_group_sets_is_staff(
        user, admin_group):
    other_user = WdaeUser.objects.create(email="email@test.com")
    admin_group.user_set.add(user, other_user)

    user.refresh_from_db()
    other_user.refresh_from_db()

    assert user.is_staff
    assert other_user.is_staff
