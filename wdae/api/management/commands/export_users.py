'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<file>'

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Filename to export users missing')
        from django.contrib.auth import get_user_model

        User = get_user_model()
        users = User.objects.all()

        with open(args[0], "w") as out:
            line = "id,email,first_name,last_name,is_staff,"\
                "is_active,researcher_id,password\n"
            out.write(line)

            for u in users:
                line = "%s,%s,%s,%s,%s,%s,%s,%s\n" % \
                    (u.id,
                     u.email, u.first_name, u.last_name,
                     u.is_staff, u.is_active, u.researcher_id, u.password)
                out.write(line)
