'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = ''
    help = 'Creates example researchers.'

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')
        from django.contrib.auth import get_user_model

        User = get_user_model()
        u, _ = User.objects.get_or_create(email='lchorbadjiev@elsys-bg.org')
        u.is_staff = False
        u.is_active = True
        u.researcher_id = '10020'
        u.set_password('paslubo')
        u.save()
        
        
        u, _ = User.objects.get_or_create(email='ivan.iossifov@gmail.com')
        u.is_staff = False
        u.is_active = True
        u.researcher_id = '10021'
        u.set_password('pasivan')
        u.save()

        u, _ = User.objects.get_or_create(email='researcher@iossifovlab.com')
        u.is_staff = False
        u.is_active = True
        u.researcher_id = '10022'
        u.set_password('passecret')
        u.save()
