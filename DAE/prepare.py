#!/usr/bin/env python
'''
Created on Aug 25, 2016

@author: lubo
'''
import sys
import argparse

from pheno.prepare.pheno_prepare import prepare_pheno_db_cache,\
    check_pheno_db_cache, prepare_agre_pheno_db, prepare_agre_pheno_db_meta,\
    prepare_vip_pheno_db, prepare_vip_pheno_db_common
from pheno.prepare.meta_probands import PrepareMetaProbands
from pheno.prepare.default_filters import PrepareDefaultFilters


def parse_arguments(argv=sys.argv[1:]):
    pass

CACHES = [
    'all',
    'pheno_db',
    'pheno_db_meta',
    'pheno_db_filters',
    'agre_pheno_db',
    'agre_pheno_db_meta',
    'vip_pheno_db',
    'vip_pheno_db_common',
]

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Tool to precompute caches for DAE.')

    parser.add_argument(
        '--recompute', '-r',
        dest='recompute',
        action='store_true',
        help='recomputes caches')

    parser.add_argument(
        '--check', '-c',
        dest='check',
        action='store_true',
        help='checks caches')

    parser.add_argument(
        'cache',
        help='caches to recompute; choose from {}'.format(
            ', '.join(["'{}'".format(c) for c in CACHES])
        ),
        choices=CACHES,
        default='all',
        nargs='+')

    # Process arguments
    args = parser.parse_args()

    if 'pheno_db' in args.cache or 'all' in args.cache:
        if args.recompute:
            prepare_pheno_db_cache()
        if args.check:
            check_pheno_db_cache()

    if 'pheno_db_meta' in args.cache or 'all' in args.cache:
        if args.recompute:
            p = PrepareMetaProbands()
            p.prepare()

    if 'pheno_db_filters' in args.cache or 'all' in args.cache:
        if args.recompute:
            p = PrepareDefaultFilters()
            p.prepare()

    if 'agre_pheno_db' in args.cache or 'all' in args.cache:
        if args.recompute:
            prepare_agre_pheno_db()

    if 'agre_pheno_db_meta' in args.cache or 'all' in args.cache:
        if args.recompute:
            prepare_agre_pheno_db_meta()

    if 'vip_pheno_db' in args.cache or 'all' in args.cache:
        if args.recompute:
            prepare_vip_pheno_db()

    if 'vip_pheno_db_common' in args.cache or 'all' in args.cache:
        if args.recompute:
            prepare_vip_pheno_db_common()

