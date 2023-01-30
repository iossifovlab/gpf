from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import csv
import sys
from .export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    help = "Export all users to stdout/csv file."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def handle_user(self, user, writer):
        groups_str = ":".join(self.get_visible_groups(user))

        if user.is_active:
            password = user.password
        else:
            password = ""

        writer.writerow(
            {
                "Email": user.email,
                "Name": user.name,
                "Groups": groups_str,
                "Password": password,
            }
        )

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()

        if options["file"]:
            csvfile = open(options["file"], "w")
        else:
            csvfile = sys.stdout

        fieldnames = ["Email", "Name", "Groups", "Password"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for user in users:
            self.handle_user(user, writer)

        if options["file"]:
            csvfile.close()
            print("\033[92m" + "Successfully exported the users!" + "\033[0m")
