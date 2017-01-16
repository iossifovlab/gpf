'''
Created on Jan 16, 2017

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
import csv


class Command(BaseCommand):
    args = '<file>'

    def check_user_attr(self, attr, udict, user):
        uv = str(user.__getattribute__(attr))
        dv = str(udict[attr])
        if uv == dv:
            print("match: attr {} for {} match...".format(
                attr, udict['email']))
        else:
            print("NOT MATCHED: attr {} for {} DOES NOT match: "
                  "{} <-> {}...".format(
                      attr, udict['email'], uv, dv))

    def check_user(self, udict, user):
        for attr in ['first_name', 'last_name', 'is_staff',
                     'is_active', 'researcher_id', 'password']:
            self.check_user_attr(attr, udict, user)

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Filename with users to import is missing')
        from django.contrib.auth import get_user_model

        User = get_user_model()

        with open(args[0], 'rb') as csvfile:
            reader = csv.DictReader(csvfile)

            for ud in reader:
                email = ud['email']
                print("")
                users_found = User.objects.filter(email=email)
                if len(users_found) >= 1:
                    print("user: {} found".format(email))
                    self.check_user(ud, users_found[0])
                else:
                    print("creating user: {}".format(email))
                    u, _ = User.objects.get_or_create(email=email)
                    u.is_staff = ud['is_staff'] == 'True'
                    u.is_active = ud['is_active'] == 'True'
                    if ud['researcher_id'] == 'None' or \
                            ud['researcher_id'] == "":
                        pass
                    else:
                        u.researcher_id = ud['researcher_id']
                    u.first_name = ud['first_name']
                    u.last_name = ud['last_name']
                    u.set_password(ud['password'])
                    u.save()
