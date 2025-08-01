import csv
from typing import Any

from django.contrib.auth.models import BaseUserManager
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)

from users_api.models import WdaeUser

from .import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    """Add users from a CSV file."""

    help = (
        "Add users from csv. "
        "Required column names for the csv file - Email."
        "Optional column names - Groups, Name, Password"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("file", type=str)

    def handle(self, *_args: Any, **options: Any) -> None:
        try:
            with open(options["file"], "r") as csvfile:
                csv_reader = csv.DictReader(csvfile)
                users = list(csv_reader)
                for user in users:
                    email = BaseUserManager.normalize_email(user["Email"])
                    if WdaeUser.objects.filter(email=email).exists():
                        print(f"User {email} already exists")
                    else:
                        self.handle_user(user)
            print(
                "\033[92m"
                "Successfully added the users from the file!"
                "\033[0m")
        except csv.Error as exc:
            raise CommandError(
                f'There was a problem while reading "{options["file"]}"',
            ) from exc
        except OSError as exc:
            raise CommandError(f'File "{options["file"]}" not found') from exc
