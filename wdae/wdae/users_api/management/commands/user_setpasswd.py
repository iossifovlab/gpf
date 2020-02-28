from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    args = "<email>"
    help = "Changes the password of user"

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("One argument is required")

        UserModel = get_user_model()
        try:
            call_command(
                "changepassword", username=args[0], stdout=self.stdout
            )
            user = UserModel.objects.get(email=args[0])
            user.is_active = True
            user.save()
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
