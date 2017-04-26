'''
Created on Jun 3, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from users.management.commands.import_researchers import ImportResearchersCommand
import csv


class Command(ImportResearchersCommand):
    pass
