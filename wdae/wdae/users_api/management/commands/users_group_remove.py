from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Remove user from group(s)"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("groups", type=str)

    def handle(self, *args, **options):
        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=options["email"])
            groups = set(options["groups"].split(":"))
            group_objects = []

            for group_name in groups:
                print(f"Collecting group '{group_name}'...")
                group_objects.append(Group.objects.get(name=group_name))

            for group in group_objects:
                group.user_set.remove(user)
            print("\033[92m" + "Successfully removed group(s)." + "\033[0m")
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
        except Group.DoesNotExist:
            raise CommandError("Group not found")
