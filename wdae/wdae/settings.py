'''
Created on Sep 2, 2015

@author: lubo
'''
from .default_settings import *  # @UnusedWildImport

ALLOWED_HOSTS += ['localhost']


INSTALLED_APPS += [
    'corsheaders',
]


MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

CORS_ORIGIN_WHITELIST = [
    'localhost:8000',
    '127.0.0.1:9000',
    'localhost:4200',
    '127.0.0.1:4200',
]

CORS_ALLOW_CREDENTIALS = True
