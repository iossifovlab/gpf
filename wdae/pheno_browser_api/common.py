'''
Created on May 24, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
import os

from django.conf import settings

# from DAE import pheno
from precompute.filehash import sha256sum


class PhenoBrowserCommon(object):

    @staticmethod
    def get_cache_dir(dbname):
        cache_dir = getattr(
            settings,
            "PHENO_BROWSER_CACHE",
            None)
        dbdir = os.path.join(cache_dir, dbname)
        return dbdir

    @staticmethod
    def get_cache_hashsum(dbname):
        hashfile = os.path.join(
            PhenoBrowserCommon.get_cache_dir(dbname),
            '{}.hash'.format(dbname))
        if not os.path.exists(hashfile):
            return ''
        with open(hashfile, 'r') as f:
            return f.read()

    @staticmethod
    def get_db_hashsum(dbname):
        dbfilename = pheno.get_dbfile(dbname)
        return PhenoBrowserCommon.calc_dbfile_hashsum(dbfilename)

    @staticmethod
    def calc_dbfile_hashsum(dbfilename):
        assert os.path.exists(dbfilename)

        base, _ext = os.path.splitext(dbfilename)
        hashfilename = '{}.hash'.format(base)
        if not os.path.exists(hashfilename):
            hashsum = sha256sum(dbfilename)
            with open(hashfilename, 'w') as f:
                f.write(hashsum)
        else:
            dbtime = os.path.getmtime(dbfilename)
            hashtime = os.path.getmtime(hashfilename)
            if hashtime >= dbtime:
                with open(hashfilename, 'r') as f:
                    hashsum = f.read().strip()
            else:
                hashsum = sha256sum(dbfilename)
                with open(hashfilename, 'w') as f:
                    f.write(hashsum)
        return hashsum

    @staticmethod
    def save_cache_hashsum(dbname):
        hashfile = os.path.join(
            PhenoBrowserCommon.get_cache_dir(dbname),
            '{}.hash'.format(dbname))
        with open(hashfile, 'w') as f:
            hashsum = PhenoBrowserCommon.get_db_hashsum(dbname)
            f.write(hashsum)

    @staticmethod
    def should_recompute(dbname):
        if not os.path.exists(pheno.get_dbfile(dbname)):
            return True
        existing_hashsum = PhenoBrowserCommon.get_cache_hashsum(dbname)
        actual_hashsum = PhenoBrowserCommon.get_db_hashsum(dbname)
        return existing_hashsum != actual_hashsum
