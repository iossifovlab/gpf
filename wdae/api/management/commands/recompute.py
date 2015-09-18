'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from api.precompute import register


class Command(BaseCommand):
    args = '<file> <file> ...'
    help = '''Creates researchers from csv. Column names for the csv file -
first name, last name, email and researcher_id.'''

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        reg = register.get_register()
        reg.recompute()
