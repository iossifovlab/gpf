from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from .import_base import ImportUsersBase


class Command(BaseCommand, ImportUsersBase):
    help = "Create new user"

    def add_arguments(self, parser):
        parser.add_argument(
            "-g",
            action="store",
            dest="groups",
            default="",
            help="Add users to this group(s). Seperated by a colon e.g."
            "group1:group2:group3",
        )

        parser.add_argument(
            "-n",
            action="store",
            dest="name",
            default="",
            help="Sets the name of the user",
        )

        parser.add_argument(
            "-p",
            action="store",
            dest="password",
            const=None,
            nargs="?",
            help="Sets the password of the user",
        )

        parser.add_argument("email", help="The emails of the new user")

    def handle(self, *args, **options):
        UserModel = get_user_model()
        if UserModel.objects.filter(email=options["email"]).exists():
            raise CommandError("User exists")

        res = {
            "Email": options["email"],
            "Name": options["name"],
            "Groups": options["groups"],
        }

        user = self.handle_user(res)

        if options["password"] is None:
            call_command(
                "changepassword", username=options["email"], stdout=self.stdout,
            )
        else:
            user.set_password(options["password"])
            user.is_active = True
            user.save()
        print("\033[92m" + "Successfully created a new user!" + "\033[0m")
