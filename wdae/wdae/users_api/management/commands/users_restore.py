import csv
import os
from users_api.models import WdaeUser
from django.core.management.base import BaseCommand, CommandError
from .import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    help = (
        "Delete all users and adds new ones from csv. "
        "Required column names for the csv file - Email. "
        "Optional column names - Groups, Name, Password"
    )

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
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
                + "\033[0m"
            )

        except csv.Error:
            raise CommandError(
                'There was a problem while reading "%s"' % args[0]
            )
        except IOError:
            raise CommandError('File "%s" not found' % args[0])
