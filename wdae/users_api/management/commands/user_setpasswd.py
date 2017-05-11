from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. ' \
        'Required column names for the csv file - LastName, Email and Id.'

    def handle(self, *args, **options):
        if(len(args) != 2):
            raise CommandError('Two arguments are required')

        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=args[0])
            user.set_password(args[1])
            user.is_active = True
            user.save()
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
