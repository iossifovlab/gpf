'''
Created on May 24, 2017

@author: lubo
'''
import os
import traceback
from DAE import pheno

from django.core.management.base import BaseCommand, CommandError
from precompute.filehash import sha256sum
from pheno_browser.prepare_data import PreparePhenoBrowserBase
from pheno_browser_api.common import get_cache_dir


class Command(BaseCommand):
    args = ''
    help = 'Rebuild pheno browser static figures cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--force',
            action='store_const',
            dest='force',
            default=False,
            help='Force recalculation of static resources',
            const=True
        )

    def get_cache_hashsum(self, dbname):
        hashfile = os.path.join(
            get_cache_dir(dbname),
            '{}.hash'.format(dbname))
        if not os.path.exists(hashfile):
            return ''
        with open(hashfile, 'r') as f:
            return f.read()

    def save_cache_hashsum(self, dbname):
        hashfile = os.path.join(
            get_cache_dir(dbname),
            '{}.hash'.format(dbname))
        with open(hashfile, 'w') as f:
            hashsum = self.get_db_hashsum(dbname)
            f.write(hashsum)

    def get_db_hashsum(self, dbname):
        dbfilename = pheno.get_dbfile(dbname)
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

    def should_recompute(self, dbname):
        existing_hashsum = self.get_cache_hashsum(dbname)
        actual_hashsum = self.get_db_hashsum(dbname)
        return existing_hashsum != actual_hashsum

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected arguments passed')

        force = options.get('force', False)

        try:
            pheno_db_names = pheno.get_pheno_db_names()
            for dbname in pheno_db_names:
                if dbname != 'vip':
                    continue

                print("checking pheno browser cache for {}".format(dbname))
                if not force and not self.should_recompute(dbname):
                    print("\tcache OK")
                    continue
                print("\tcache RECOMPUTE")
                output_dir = get_cache_dir(dbname)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                prep = PreparePhenoBrowserBase(dbname, output_dir)
                prep.run()
                self.save_cache_hashsum(dbname)

        except Exception:
            traceback.print_exc()
            raise CommandError("Unexpected error")
