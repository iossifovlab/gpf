from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)

from .export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    """Show user information."""
    help = "Show all information about user"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        try:
            # pylint: disable=invalid-name
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            groups: str = ",".join(self.get_visible_groups(
                cast(AbstractUser, user)))

            print(
                f"User email: {user.email}\n"
                f"name: {user.name}\n"
                f"groups: {groups}\n"
                f"password: {user.password}",
            )
        except UserModel.DoesNotExist as exc:
            raise CommandError("User not found") from exc
