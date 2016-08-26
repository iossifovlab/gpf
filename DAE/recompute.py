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
from pheno.precompute.values import PrepareFloatValues

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


def recompute_pheno_float_values_cache():
    print(LINE)
    print("recomputing pheno db float/integer values caches")
    print(LINE)

    p10 = PrepareVariables()
    p10.prepare()

    p20 = PrepareFloatValues()
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Tool to precompute caches for DAE.")

    parser.add_argument(
        "--recompute",
        dest="recompute",
        action="store_true",
        help="recomputes caches")

    parser.add_argument(
        "--check",
        dest="check",
        action="store_true",
        help="checks caches")

    parser.add_argument(
        "cache",
        help="caches to recompute",
        nargs='?')

    # Process arguments
    args = parser.parse_args()
    if args.cache == 'pheno_families' or args.cache == 'all':
        if args.recompute:
            recompute_pheno_families_cache()
        if args.check:
            check_pheno_families_cache()

    if args.cache == 'pheno_variables' or args.cache == 'all':
        if args.recompute:
            recompute_pheno_variables_cache()

    if args.cache == 'pheno_values' or args.cache == 'all':
        if args.recompute:
            recompute_pheno_float_values_cache()
