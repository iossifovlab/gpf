'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from users.management.commands import import_researchers
import csv


class Command(import_researchers.Command):
    pass
