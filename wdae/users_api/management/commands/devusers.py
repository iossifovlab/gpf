'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<file> <file> ...'

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')
        from django.contrib.auth import get_user_model

        User = get_user_model()
        u = User.objects.create_user(email='admin@iossifovlab.com',
                                     password='secret')
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save()

        u = User.objects.create_user(email='research@iossifovlab.com',
                                     password='secret')
        u.is_staff = False
        u.is_active = True
        u.is_superuser = False
        u.save()

        u = User.objects.create_user(email='vip@iossifovlab.com',
                                     password='secret')
        u.is_staff = False
        u.is_active = True
        u.is_superuser = False
        u.save()

        u = User.objects.create_user(email='ssc@iossifovlab.com',
                                     password='secret')
        u.is_staff = False
        u.is_active = True
        u.is_superuser = False
        u.save()
