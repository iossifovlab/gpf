import csv
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from users_api.models import WdaeUser

from .import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    """Restore users command."""

    help = (
        "Delete all users and adds new ones from csv. "
        "Required column names for the csv file - Email. "
        "Optional column names - Groups, Name, Password"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("file", type=str)

    def handle(self, *args: Any, **options: Any) -> None:
        csvfilename = options["file"]
        assert os.path.exists(csvfilename)

        try:
            with open(csvfilename, "rt") as csvfile:
                resreader = csv.DictReader(csvfile)
                WdaeUser.objects.all().delete()
                for res in resreader:
                    self.handle_user(res)
            print(
                "\033[92m"
                + "Successfully restored users from file!"
                + "\033[0m",
            )

        except csv.Error as ex:
            raise CommandError(
                f"There was a problem while reading {args[0]}",
            ) from ex
        except OSError as ex:
            raise CommandError(f"File {args[0]} not found") from ex
