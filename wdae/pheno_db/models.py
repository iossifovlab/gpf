'''
Created on Aug 10, 2016

@author: lubo
'''
from django.db import models


class VariableDescriptor(models.Model):
    source = models.CharField(max_length='32')
    table_name = models.CharField(max_length='64')
    variable_name = models.CharField(max_length='127')
    variable_category = models.CharField(max_length='127', null=True)

    variable_id = models.CharField(max_length='255', unique=True)
    domain = models.CharField(max_length='127')
    domain_choice_label = models.CharField(max_length='255', null=True)
    measurement_scale = models.CharField(max_length='32')
    regards_mother = models.NullBooleanField()
    regards_father = models.NullBooleanField()
    regards_proband = models.NullBooleanField()
    regards_sibling = models.NullBooleanField()
    regards_family = models.NullBooleanField()
    regards_other = models.NullBooleanField()
    variable_notes = models.TextField(null=True)

    is_calculated = models.BooleanField()
    calculation_documentation = models.TextField(null=True)
