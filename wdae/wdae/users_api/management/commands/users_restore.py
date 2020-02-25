import csv
from users_api.models import WdaeUser
from django.core.management.base import BaseCommand, CommandError
from .import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    args = "<file>"
    help = (
        "Deletes all users and adds new ones from csv. "
        "Required column names for the csv file - Email."
        "Optional column names - Groups, Name, Password"
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Exactly one argument is required")

        try:
            with open(args[0], "rb") as csvfile:
                resreader = csv.DictReader(csvfile)
                WdaeUser.objects.all().delete()
                for res in resreader:
                    self.handle_user(res)

        except csv.Error:
            raise CommandError(
                'There was a problem while reading "%s"' % args[0]
            )
        except IOError:
            raise CommandError('File "%s" not found' % args[0])
