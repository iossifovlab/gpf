"""
Created on Jun 3, 2015

@author: lubo
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import csv
import sys
from .export_base import ExportUsersBase


class Command(BaseCommand, ExportUsersBase):
    args = "[file]"
    help = "Export all users to stdout/csv file."

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
        if len(args) > 1:
            raise CommandError("Expected maximum one argument")

        User = get_user_model()
        users = User.objects.all()

        if len(args) == 1:
            csvfile = open(args[0], "w")
        else:
            csvfile = sys.stdout

        fieldnames = ["Email", "Name", "Groups", "Password"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for user in users:
            self.handle_user(user, writer)

        if len(args) == 1:
            csvfile.close()
