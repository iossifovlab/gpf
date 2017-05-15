from django.core.management.base import BaseCommand, CommandError
from import_base import ImportUsersBase
from django.contrib.auth import get_user_model
from django.core.management import call_command


class Command(BaseCommand, ImportUsersBase):
    args = '[-n <name>] [-g <groups>] <email>'
    help = 'Creates new user'

    def add_arguments(self, parser):
        parser.add_argument(
            '-g',
            action='store',
            dest='groups',
            default='',
            help='Add users to this group(s). Seperated by a colon e.g.'
            'group1:group2:group3',
        )

        parser.add_argument(
            '-n',
            action='store',
            dest='name',
            default='',
            help='Sets the name of the user',
        )

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument required')

        UserModel = get_user_model()
        if UserModel.objects.filter(email=args[0]).exists():
            raise CommandError('User exists')

        res = {
            'Email': args[0],
            'Name': options['name'],
            'Groups': options['groups']
        }
        self.handle_user(res)

        call_command('changepassword', username=args[0], stdout=self.stdout)
