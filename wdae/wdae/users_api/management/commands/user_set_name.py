from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Changes the name of the user with the given email"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("new_name", type=str)

    def handle(self, *args, **options):
        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            user.name = options["new_name"]
            user.save()
            print("\033[92m" + "Successfully renamed the user." + "\033[0m")
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
