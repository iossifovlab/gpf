from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deletes user"

    def add_arguments(self, parser):
        parser.add_argument("-email", type=str)

    def handle(self, *args, **options):
        UserModel = get_user_model()
        users = UserModel.objects.filter(groups__name=options["email"])
        if not users:
            raise CommandError("User not found!")
        for user in users:
            user.delete()
        print("\033[92m" + "Successfully deleted the user." + "\033[0m")
