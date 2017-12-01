'''
Created on May 24, 2017

@author: lubo
'''
import os
import traceback
from DAE import pheno

from django.core.management.base import BaseCommand, CommandError
from pheno_browser.prepare_data import PreparePhenoBrowserBase
from pheno_browser_api.common import PhenoBrowserCommon
from pheno.pheno_regression import PhenoRegression


class Command(BaseCommand, PhenoBrowserCommon):
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

        parser.add_argument(
            '-p', '--pheno',
            action='store',
            dest='pheno',
            help='Specify with pheno db to use. '
            'By default works on all configured pheno DBs')

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError('Unexpected arguments passed')

        force = options.get('force', False)
        pheno_db = options.get('pheno', None)
        try:
            if pheno_db is not None:
                pheno_db_names = [pheno_db]
            else:
                pheno_db_names = pheno.get_pheno_db_names()

            print("going to recaclulate {}".format(pheno_db_names))

            for pheno_name in pheno_db_names:
                print("checking pheno browser cache for {}".format(pheno_name))
                if not force and not self.should_recompute(pheno_name):
                    print("\tcache OK")
                    continue
                print("\tcache RECOMPUTING")
                output_dir = PhenoBrowserCommon.get_cache_dir(pheno_name)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                pheno_db = pheno.get_pheno_db(pheno_name)
                pheno_regression = PhenoRegression.build(pheno_name)

                prep = PreparePhenoBrowserBase(
                    pheno_name, pheno_db, pheno_regression, output_dir)
                prep.run()
                self.save_cache_hashsum(pheno_name)

        except Exception:
            traceback.print_exc()
            raise CommandError("Unexpected error")
