from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)


class Command(BaseCommand):
    """Delete user command."""

    help = "Delete user"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        # pylint: disable=invalid-name
        UserModel = get_user_model()
        users = UserModel.objects.filter(email=options["email"])
        if not users:
            raise CommandError("User not found!")
        for user in users:
            user.delete()
        print("\033[92mSuccessfully deleted the user.\033[0m")
