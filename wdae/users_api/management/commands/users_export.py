'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import csv
import sys


class Command(BaseCommand):
    args = '<file>'

    def handle_user(self, user, writer):
        groups = set(user.groups.values_list('name', flat=True).all())
        skip_groups = list(user.DEFAULT_GROUPS_FOR_USER)
        skip_groups.append(user.email)

        groups.difference_update(skip_groups)

        if user.is_superuser:
            groups.add("superuser")
        groups_str = ":".join(groups)

        if user.is_active:
            password = user.password
        else:
            password = ""

        writer.writerow({
            "Email": user.email,
            "Name": user.name,
            "Groups": groups_str,
            "Password": password
        })

    def handle(self, *args, **options):
        if(len(args) > 1):
            raise CommandError('Expected maximum one argument')

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
