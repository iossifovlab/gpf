import tempfile
import os

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from users_api.management.commands.export_base import ExportUsersBase


class UsersApiCommandsTests(TestCase):
    def test_users_export(self):
        User = get_user_model()
        new_user = User.objects.create_user(
            "john@test.abv", name="user john"
        )
        new_admin_user = User.objects.create_user(
            "shefa@test.abv", name="shf", password="verysecret"
        )
        new_group = Group.objects.create(name="testgroup")
        new_user.groups.add(new_group)
        new_admin_user.groups.add(new_group)
        new_admin_user.groups.add(Group.objects.create(name="admin"))

        groups_str = ":".join(
            ExportUsersBase().get_visible_groups(new_admin_user)
        )

        expected_output = (
            "Email,Name,Groups,Password"
            "\njohn@test.abv,user john,testgroup,"
            f"\nshefa@test.abv,shf,{groups_str},{new_admin_user.password}"
            "\n"
        )
        temp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        call_command("users_export", file=temp.name)
        try:
            self.assertEqual(temp.read(), expected_output)
        finally:
            temp.close()
            os.unlink(temp.name)

    def test_users_restore(self):
        User = get_user_model()
        input_csv = (
            "Email,Name,Groups,Password"
            "\njohn@test.abv,user john,testgroup,"
            "\nshefa@test.abv,shf,testgroup:admin,123123"
            "\n"
        )
        temp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        temp.write(input_csv)
        temp.close()
        call_command("users_restore", temp.name)
        try:
            second_user = User.objects.last()
            self.assertEqual(len(User.objects.all()), 2)
            self.assertEqual(
                second_user.email, "shefa@test.abv"
            )
            self.assertEqual(
                second_user.name, "shf"
            )
            self.assertEqual(
                second_user.is_active, True
            )
            self.assertEqual(
                second_user.is_staff, True
            )
            self.assertEqual(
                len(second_user.groups.all()), 2
            )
        finally:
            os.unlink(temp.name)