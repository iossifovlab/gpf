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
    'http://localhost:8000',
    'http://127.0.0.1:9000',
    'http://localhost:4200',
    'http://127.0.0.1:4200',
]

CORS_ALLOW_CREDENTIALS = True
