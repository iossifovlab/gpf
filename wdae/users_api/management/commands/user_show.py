from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. ' \
        'Required column names for the csv file - LastName, Email and Id.'

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('One argument is required')

        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=args[0])

            groups = ",".join(self.get_visible_groups(user))

            print("User email: {} name: {} groups: {} password:{}".format(
                  user.email, user.name, groups, user.password))
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
