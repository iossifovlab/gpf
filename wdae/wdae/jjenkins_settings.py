'''
Created on Dec 2, 2015

@author: lubo
'''
from wdae.default_settings import *  # @UnusedWildImport


INSTALLED_APPS += [
    'django_jenkins',
]

PROJECT_APPS = ['api', 'pheno_report', 'gene_weights', 'helpers', 'families']
