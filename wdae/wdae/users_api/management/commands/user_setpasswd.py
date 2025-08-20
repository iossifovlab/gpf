from typing import Any

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)


class Command(BaseCommand):
    """Change the password of a user with the given email."""

    help = "Change the password of a user with the given email"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        # pylint: disable=invalid-name
        UserModel = get_user_model()
        try:
            call_command(
                "changepassword", username=options["email"],
                stdout=self.stdout,
            )
            user = UserModel.objects.get(email=options["email"])
            user.is_active = True
            user.save()
            print(
                "\033[92m"
                "Successfully changed the user's password."
                "\033[0m",
            )
        except UserModel.DoesNotExist as exc:
            raise CommandError("User not found") from exc
