from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Add user into group(s)"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("groups", type=str)

    def handle(self, *args, **options):
        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            groups = set(options["groups"].split(":"))
            for group_name in groups:
                if group_name == "":
                    continue
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(user)
            print("\033[92m" + "Successfully added group(s)." + "\033[0m")
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
