#!/usr/bin/env python
'''
Created on Aug 25, 2016

@author: lubo
'''
import sys
import argparse

from pheno.precompute.families import PrepareIndividuals,\
    PrepareIndividualsGender, PrepareIndividualsSSCPresent,\
    PrepareIndividualsGenderFromSSC, CheckIndividualsGenderToSSC
from pheno.precompute.variables import PrepareVariables
from pheno.precompute.values import PrepareRawValues,\
    PrepareVariableDomainRanks, PrepareValueClassification

LINE = "--------------------------------------------------------------------"


def recompute_pheno_families_cache():
    print(LINE)
    print("recomputing pheno db family caches")
    print(LINE)

    p10 = PrepareIndividuals()
    p10.prepare()

    p20 = PrepareIndividualsGender()
    p20.prepare()

    p30 = PrepareIndividualsSSCPresent()
    p30.prepare()

    p40 = PrepareIndividualsGenderFromSSC()
    p40.prepare()

    print(LINE)


def recompute_pheno_variables_cache():
    print(LINE)
    print("recomputing pheno db variable dictionary caches")
    print(LINE)

    p10 = PrepareVariables()
    p10.prepare()

    print(LINE)


def recompute_pheno_raw_values_cache():
    print(LINE)
    print("recomputing pheno db raw values caches")
    print(LINE)

    p20 = PrepareRawValues()
    p20.prepare()

    print(LINE)


def recompute_pheno_variables_ranks_cache():
    print(LINE)
    print("recomputing pheno db variables ranks caches")
    print(LINE)

    p20 = PrepareVariableDomainRanks()
    p20.prepare()

    print(LINE)


def classify_pheno_variables():
    print(LINE)
    print("recomputing pheno db variable classification caches")
    print(LINE)

    p20 = PrepareValueClassification()
    p20.prepare()

    print(LINE)


def check_pheno_families_cache():
    print(LINE)
    print("checking pheno db caches")
    print(LINE)

    ch10 = CheckIndividualsGenderToSSC()
    ch10.check()

    print(LINE)


def parse_arguments(argv=sys.argv[1:]):
    pass

CACHES = [
    'all',
    'pheno_families',
    'pheno_variables',
    'pheno_raw_values',
    'pheno_variables_ranks',
    'pheno_values',
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

    if 'pheno_families' in args.cache or 'all' in args.cache:
        if args.recompute:
            recompute_pheno_families_cache()
        if args.check:
            check_pheno_families_cache()

    if 'pheno_variables' in args.cache or 'all' in args.cache:
        if args.recompute:
            recompute_pheno_variables_cache()

    if 'pheno_raw_values' in args.cache or 'all' in args.cache:
        if args.recompute:
            recompute_pheno_raw_values_cache()

    if 'pheno_variables_ranks' in args.cache or 'all' in args.cache:
        if args.recompute:
            recompute_pheno_variables_ranks_cache()

    if 'pheno_values' in args.cache or 'all' in args.cache:
        if args.recompute:
            classify_pheno_variables()
