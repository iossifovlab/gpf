import csv

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from api.models import Researcher

class Command(BaseCommand):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. Column names for the csv file - first name, last name, email and researcher_id.'

    def handle(self, *args, **options):
        if(len(args) < 1):
            raise CommandError('At least one argument is required')
        for csv_file in args:
            try:
                with open(csv_file, 'rb') as csvfile:
                    resreader = csv.DictReader(csvfile)

                    for res in resreader:
                        res_instance = Researcher()
                        res_instance.email = res['email']
                        res_instance.unique_number = str(res['researcher id'])
                        res_instance.first_name = res['first name']
                        res_instance.last_name = res['last name']
                        try:
                            res_instance.save()
                        except IntegrityError, i:
                            self.stdout.write('Researcher {0} {1} {2} {3} already exists, skipped.' \
                                             .format(res_instance.first_name, res_instance.last_name, \
                                                     res_instance.email, res_instance.unique_number))
            except csv.Error:
                raise CommandError('There was a problem while reading "%s"' % csv_file)
            except IOError:
                raise CommandError('File "%s" not found' % csv_file)
