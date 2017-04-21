'''
Created on Aug 10, 2016

@author: lubo
'''
from django.db import models


class Dataset(models.Model):
    dataset_id = models.TextField()

    class Meta:
        permissions = (
            ('view', 'View dataset'),
        )
