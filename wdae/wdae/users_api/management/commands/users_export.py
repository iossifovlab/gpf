import csv
import sys
import io

from typing import Any, TextIO, Union

from django.core.management.base import CommandParser, BaseCommand
from django.contrib.auth import get_user_model

from users_api.models import WdaeUser

from .export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    """Export users command."""

    help = "Export all users to stdout/csv file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", type=str)

    def handle_user(self, user: WdaeUser, writer: csv.DictWriter) -> None:
        """Handle user export."""
        groups_str = ":".join(self.get_visible_groups(user))

        if user.is_active:
            password = user.password
        else:
            password = ""

        writer.writerow(
            {
                "Email": user.email,
                "Name": user.name,
                "Groups": groups_str,
                "Password": password,
            }
        )

    def handle(self, *args: Any, **options: Any) -> None:
        users = get_user_model().objects.all()

        csvfile: Union[TextIO, io.TextIOWrapper]
        if options["file"]:
            # pylint: disable=consider-using-with
            csvfile = open(options["file"], "w")
        else:
            csvfile = sys.stdout

        fieldnames = ["Email", "Name", "Groups", "Password"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for user in users:
            self.handle_user(user, writer)

        if options["file"]:
            csvfile.close()
            print("\033[92m" + "Successfully exported the users!" + "\033[0m")
