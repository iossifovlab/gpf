'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from api.models import Researcher

class Command(BaseCommand):
    args = '<file> <file> ...'
    help = 'Creates researchers from csv. Column names for the csv file - first name, last name, email and researcher_id.'

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')
        from django.contrib.auth import get_user_model

        User = get_user_model()
        u, _ = User.objects.get_or_create(email='admin@iossifovlab.com')
        u.is_staff = True
        u.is_active = True
        
        u.set_password('secret')
        u.save()
        
        
        u, _ = User.objects.get_or_create(email='research@iossifovlab.com')
        u.is_staff = False
        u.is_active = True
        u.researcher_id = '10001'
        u.set_password('secret')
        u.save()
