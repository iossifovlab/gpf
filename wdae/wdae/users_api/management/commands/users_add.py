import csv
from users_api.models import WdaeUser
from django.contrib.auth.models import BaseUserManager
from django.core.management.base import BaseCommand, CommandError
from .import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    help = (
        "Add users from csv. "
        "Required column names for the csv file - Email."
        "Optional column names - Groups, Name, Password"
    )

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        try:
            with open(options["file"], "r") as csvfile:
                csv_reader = csv.DictReader(csvfile)
                users = list(csv_reader)
                for user in users:
                    email = BaseUserManager.normalize_email(user["Email"])
                    if WdaeUser.objects.filter(email=email).exists():
                        print("User {} already exists".format(email))
                    else:
                        self.handle_user(user)
            print(
                "\033[92m"
                "Successfully added the users from the file!"
                "\033[0m")
        except csv.Error:
            raise CommandError(
                'There was a problem while reading "%s"' % options["file"]
            )
        except IOError:
            raise CommandError('File "%s" not found' % options["file"])
