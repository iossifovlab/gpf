from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from .export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    help = "Show all information about user"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            groups = ",".join(self.get_visible_groups(user))

            print(
                f"User email: {user.email}\n"
                f"name: {user.name}\n"
                f"groups: {groups}\n"
                f"password: {user.password}",
            )
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
