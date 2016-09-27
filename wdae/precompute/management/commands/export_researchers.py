'''
Created on Sep 20, 2016

@author: lubo
'''
from django.contrib.auth.models import BaseUserManager
from django.core.management.base import BaseCommand, CommandError

from api.models import ResearcherId


class Command(BaseCommand):
    args = '<file>'

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Filename to export researchers missing')

        with open(args[0], 'w') as out:
            out.write("Id,email,last name\n")
            res_ids = ResearcherId.objects.all()
            for res_id in res_ids:
                for res in res_id.researcher.all():
                    line = "{},{},{}\n".format(
                        res_id.researcher_id,
                        res.last_name,
                        BaseUserManager.normalize_email(res.email)
                    )
                    print(line)
                    out.write(line)
