'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import csv

class Command(BaseCommand):
    args = '<file>'

    def handle_user(self, user, writer):
        groups_str = ":".join(
            user.groups.values_list('name', flat=True).all()
        )
        researcher_ids_str = ":".join(
            user.researcherid_set.values_list('researcher_id', flat=True).all()
        )

        writer.writerow({
            "Email": user.email,
            "FirstName": user.first_name,
            "LastName": user.last_name,
            "Groups": groups_str,
            "Superuser": user.is_superuser,
            "Staff": user.is_staff,
            "Active": user.is_active,
            "Id": researcher_ids_str,
            "Password": user.password
        })

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Filename to export users missing')


        User = get_user_model()
        users = User.objects.all()

        with open(args[0], "w") as csvfile:
            fieldnames = ["Email", "FirstName", "LastName", "Groups",
                          "Superuser", "Staff", "Active", "Id",
                          "Password"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user in users:
                self.handle_user(user, writer)
