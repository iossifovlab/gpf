from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)


class Command(BaseCommand):
    """Add user to group(s) command."""
    help = "Add user into group(s)"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str)
        parser.add_argument("groups", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        try:
            # pylint: disable=invalid-name
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            groups: set[str] = set(options["groups"].split(":"))
            for group_name in groups:
                if group_name == "":
                    continue
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(user)
            print("\033[92mSuccessfully added group(s).\033[0m")
        except UserModel.DoesNotExist as exc:
            raise CommandError("User not found") from exc
