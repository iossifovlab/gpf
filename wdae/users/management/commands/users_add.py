import csv
from users.models import WdaeUser
from django.contrib.auth.models import BaseUserManager
from django.core.management.base import BaseCommand, CommandError
from import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. ' \
        'Required column names for the csv file - LastName, Email and Id.'

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument is required')

        try:
            with open(args[0], 'rb') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                should_add_users = True
                users = list(csv_reader)
                for user in users:
                    email = BaseUserManager.normalize_email(user['Email'])
                    if WdaeUser.objects.filter(email=email).exists():
                        print("User {} already exists".format(email))
                        should_add_users = False

                if should_add_users:
                    for res in users:
                        self.handle_user(res)

        except csv.Error:
            raise CommandError(
                'There was a problem while reading "%s"' % args[0])
        except IOError:
            raise CommandError('File "%s" not found' % args[0])
