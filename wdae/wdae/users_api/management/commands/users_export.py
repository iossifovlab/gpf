import csv
import sys
from typing import Any, TextIO, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.management.base import BaseCommand, CommandParser

from users_api.models import WdaeUser

from .export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    """Export users command."""

    help = "Export all users to stdout/csv file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", type=str)

    def handle_user(self, user: WdaeUser, writer: csv.DictWriter[str]) -> None:
        """Handle user export."""
        groups_str: str = ":".join(self.get_visible_groups(
            cast(AbstractUser, user)))
        password: str = user.password if user.is_active else ""

        writer.writerow(
            {
                "Email": user.email,
                "Name": user.name,
                "Groups": groups_str,
                "Password": password,
            },
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        users = get_user_model().objects.all()

        if options["file"]:
            with open(options["file"], "w", encoding="utf-8") as csvfile:
                self._write_users_to_csv(users, csvfile)
            print("\033[92mSuccessfully exported the users!\033[0m")
        else:
            self._write_users_to_csv(users, sys.stdout)

    def _write_users_to_csv(
        self,
        users: Any,
        csvfile: TextIO,
    ) -> None:
        """Write users to CSV file."""
        fieldnames: list[str] = ["Email", "Name", "Groups", "Password"]
        writer: csv.DictWriter[str] = csv.DictWriter(
            csvfile, fieldnames=fieldnames,
        )
        writer.writeheader()

        for user in users:
            self.handle_user(user, writer)
