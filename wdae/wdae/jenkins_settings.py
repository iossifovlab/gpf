'''
Created on Aug 31, 2015

@author: lubo
'''
from .settings import *  # @UnusedWildImport


INSTALLED_APPS += [
    'django_nose',
]

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'foo' and 'bar' apps
NOSE_ARGS = [
             # '--with-coverage',
             # '--cover-package=api',
             '--verbosity=2',
]

# import os
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         "NAME": os.environ.get("DB_NAME", "seqpipe"),
#         'USER': os.environ.get("DB_USER", 'seqpipe'),
#         'PASSWORD': os.environ.get("DB_PASS", 'lae0suNu'),
#         'HOST': os.environ.get("DB_HOST", '127.0.0.1'),
#         'PORT': os.environ.get("DB_PORT", '3306'),
#     }
# }
