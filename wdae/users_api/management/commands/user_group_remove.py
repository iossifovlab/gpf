from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<email> <group>:<group>:'
    help = 'Removes user from group(s)'

    def handle(self, *args, **options):
        if(len(args) != 2):
            raise CommandError('Two arguments are required')

        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(email=args[0])

            groups = args[1].split(':')
            for group_name in set(groups):
                if group_name == "":
                    continue
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.remove(user)
        except UserModel.DoesNotExist:
            raise CommandError("User not found")
