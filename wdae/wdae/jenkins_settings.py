'''
Created on Aug 31, 2015

@author: lubo
'''
from wdae.default_settings import *  # @UnusedWildImport


INSTALLED_APPS += [
    'django_jenkins',
]

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes'
)
