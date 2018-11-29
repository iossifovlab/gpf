from builtins import range
import pytest

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


@pytest.fixture()
def users_instance_url():
    return user_url


def user_url(user_id):
    return reverse('users-detail', kwargs={'pk': user_id})


@pytest.fixture()
def user_remove_password_endpoint():
    return user_remove_password_url


def user_remove_password_url(user_id):
    return reverse('users-password-remove', kwargs={'pk': user_id})


@pytest.fixture()
def user_reset_password_endpoint():
    return user_reset_password_url


def user_reset_password_url(user_id):
    return reverse('users-password-reset', kwargs={'pk': user_id})


@pytest.fixture()
def users_bulk_add_group_url():
    return reverse('users-bulk-add-group')


@pytest.fixture()
def users_bulk_remove_group_url():
    return reverse('users-bulk-remove-group')


@pytest.fixture()
def empty_group(db):
    return Group.objects.create(name='Empty group')


@pytest.fixture()
def active_user(db, user_model):
    user = user_model.objects.create_user(email='new@new.com', password='secret')

    assert user.is_active
    return user


@pytest.fixture()
def inactive_user(db, user_model):
    user = user_model.objects.create_user(email='new@new.com')

    assert not user.is_active
    return user


@pytest.fixture()
def three_new_users(db, user_model):
    users = []
    for email_id in range(3):
        user = user_model.objects \
            .create(email='user{}@example.com'.format(email_id+1))
        users.append(user)

    return users


@pytest.fixture()
def three_users_in_a_group(db, three_new_users, empty_group):
    empty_group.user_set.add(*three_new_users)
    for user in three_new_users:
        user.refresh_from_db()

    return three_new_users, empty_group
