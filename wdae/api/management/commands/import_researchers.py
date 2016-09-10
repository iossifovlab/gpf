import csv

from django.core.management.base import BaseCommand, CommandError

from api.models import Researcher, ResearcherId
from django.contrib.auth.models import BaseUserManager


class Command(BaseCommand):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv.' \
        'Required column names for the csv file - LastName, Email and Id.'

    def load_or_create_researcher_id(self, rid):
        res_ids = ResearcherId.objects.filter(researcher_id=rid)
        if len(res_ids) == 1:
            res_id = res_ids[0]
        else:
            res_id = ResearcherId()
            res_id.researcher_id = rid
            res_id.save()
        return res_id

    def handle(self, *args, **options):
        if(len(args) < 1):
            raise CommandError('At least one argument is required')
        for csv_file in args:
            try:
                with open(csv_file, 'rb') as csvfile:
                    resreader = csv.DictReader(csvfile)

                    for res in resreader:
                        print("creating researcher:{}".format(res))

                        rid = res['Id']
                        email = BaseUserManager.normalize_email(res['Email'])

                        res_instances = Researcher.objects.filter(email=email)
                        if len(res_instances) == 1:
                            res_instance = res_instances[0]
                            researcher_ids = \
                                res_instance.researcherid_set.all()
                            researcher_id_set = set(
                                [r.researcher_id for r in researcher_ids])
                            if rid in researcher_id_set:
                                print("researcher already exists: {}".format(
                                    email))
                                continue
                            res_id = self.load_or_create_researcher_id(rid)

                            res_id.researcher.add(res_instance)
                            res_id.save()
                        else:

                            res_instance = Researcher()
                            res_instance.email = email
                            res_instance.last_name = res['LastName']
                            res_instance.save()

                            res_id = self.load_or_create_researcher_id(rid)

                            res_id.researcher.add(res_instance)
                            res_id.save()

            except csv.Error:
                raise CommandError(
                    'There was a problem while reading "%s"' % csv_file)
            except IOError:
                raise CommandError('File "%s" not found' % csv_file)
