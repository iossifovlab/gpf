# pylint: disable=W0621,C0114,C0116,W0212,W0613,missing-class-docstring
import tempfile
from typing import cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group
from django.core.management import call_command
from django.test import TestCase

from users_api.management.commands.export_base import ExportUsersBase


class UsersApiCommandsTests(TestCase):
    def test_users_export(self) -> None:
        # pylint: disable=invalid-name
        User = get_user_model()
        new_user = User.objects.create_user(  # pyright: ignore
            "john@test.abv", name="user john",
        )
        new_admin_user = User.objects.create_user(  # pyright: ignore
            "shefa@test.abv", name="shf",
            password="verysecret",  # noqa
        )
        new_group = Group.objects.create(name="testgroup")
        new_user.groups.add(new_group)
        new_admin_user.groups.add(new_group)
        new_admin_user.groups.add(Group.objects.create(name="admin"))

        groups_str = ":".join(
            ExportUsersBase().get_visible_groups(
                cast(AbstractUser, new_admin_user),
            ))

        expected_output = (
            "Email,Name,Groups,Password"
            "\njohn@test.abv,user john,testgroup,"
            f"\nshefa@test.abv,shf,{groups_str},{new_admin_user.password}"
            "\n"
        )
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            call_command("users_export", file=temp.name)
            assert temp.read() == expected_output

    def test_users_restore(self) -> None:
        # pylint: disable=invalid-name
        User = get_user_model()
        input_csv = (
            "Email,Name,Groups,Password"
            "\njohn@test.abv,user john,testgroup,"
            "\nshefa@test.abv,shf,testgroup:admin,123123"
            "\n"
        )
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(input_csv)
            temp.close()
            call_command("users_restore", temp.name)
            second_user = User.objects.last()

            assert second_user is not None

            assert len(User.objects.all()) == 2
            assert second_user.email == "shefa@test.abv"  # pyright: ignore
            assert second_user.name == "shf"  # pyright: ignore
            assert second_user.is_active is True
            assert second_user.is_staff is True  # pyright: ignore
            assert len(second_user.groups.all()) == 2  # pyright: ignore
