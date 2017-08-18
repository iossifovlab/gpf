'''
Created on May 24, 2017

@author: lubo
'''
import os

from django.conf import settings


def get_cache_dir(dbname):
    cache_dir = getattr(
        settings,
        "PHENO_BROWSER_CACHE",
        None)
    return os.path.join(cache_dir, 'pheno_browser', dbname)