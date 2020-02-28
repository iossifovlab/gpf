from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = "<email> <name>"
    help = "Changes the name of user"

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("Two arguments are required")

        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=args[0])
            user.name = args[1]
            user.save()
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
