from django.core.management.base import BaseCommand, CommandError
from import_base import ImportUsersBase
from django.contrib.auth import get_user_model


class Command(BaseCommand, ImportUsersBase):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. ' \
        'Required column names for the csv file - LastName, Email and Id.'

    def handle(self, *args, **options):
        if(len(args) < 1 or len(args) > 4):
            raise CommandError('1-4 arguments required')

        UserModel = get_user_model()
        if UserModel.objects.filter(email=args[0]).exists():
            raise CommandError('User exists')

        res = {'Email': args[0]}
        if len(args) >= 2:
            res['Name'] = args[1]
        if len(args) >= 3:
            res['Groups'] = args[2]
        self.handle_user(res)
