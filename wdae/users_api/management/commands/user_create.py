from django.core.management.base import BaseCommand, CommandError
from import_base import ImportUsersBase
from django.contrib.auth import get_user_model
from django.core.management import call_command


class Command(BaseCommand, ImportUsersBase):
    args = '<email> [<name>] [<groups>]'
    help = 'Creates new user'

    def handle(self, *args, **options):
        if(len(args) < 1 or len(args) > 3):
            raise CommandError('1-3 arguments required')

        UserModel = get_user_model()
        if UserModel.objects.filter(email=args[0]).exists():
            raise CommandError('User exists')

        res = {'Email': args[0]}
        if len(args) >= 2:
            res['Name'] = args[1]
        if len(args) >= 3:
            res['Groups'] = args[2]
        self.handle_user(res)

        call_command('changepassword', username=args[0], stdout=self.stdout)
