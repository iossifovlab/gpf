from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)


class Command(BaseCommand):
    """Change the name of a user."""

    help = "Change the name of the user with the given email"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str)
        parser.add_argument("new_name", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        try:
            # pylint: disable=invalid-name
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            user.name = options["new_name"]
            user.save()
            print("\033[92mSuccessfully renamed the user.\033[0m")
        except UserModel.DoesNotExist as exc:
            raise CommandError("User not found") from exc
