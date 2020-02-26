from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<email>'
    help = 'Deletes user'

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('One argument is required')

        try:
            UserModel = get_user_model()
            users = UserModel.objects.filter(groups__name=args[0])
            for user in users:
                user.delete()
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
