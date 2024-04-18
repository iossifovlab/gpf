from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from users_api.models import AuthenticationLog

from .import_base import ImportUsersBase


class Command(ImportUsersBase, BaseCommand):
    help = "Remove a lockout on a user's account."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=options["email"])
            AuthenticationLog(
                email=user.email,
                time=timezone.now(),
                failed_attempt=0,
            ).save()
            print(
                "\033[92m"
                + "Successfully unlocked the user account."
                + "\033[0m",
            )
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
