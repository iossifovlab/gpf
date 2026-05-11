from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)


class Command(BaseCommand):
    """Remove user from group(s)"""

    help = "Remove user from group(s)"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str)
        parser.add_argument("groups", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa:ARG002
        try:
            UserModel = get_user_model()  # pylint: disable=invalid-name
            user = UserModel.objects.get(email=options["email"])
            groups: set[str] = set(options["groups"].split(":"))
            group_objects: list[Group] = []

            for group_name in groups:
                print(f"Collecting group '{group_name}'...")
                group_objects.append(Group.objects.get(name=group_name))

            for group in group_objects:
                group.user_set.remove(user)
            print("\033[92m" + "Successfully removed group(s)." + "\033[0m")
        except UserModel.DoesNotExist as exc:
            raise CommandError("User not found") from exc
        except Group.DoesNotExist as exc:
            raise CommandError("Group not found") from exc
