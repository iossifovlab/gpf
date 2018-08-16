#!/usr/bin/env python
from __future__ import print_function

import argparse
import sys

from display_variants import join_line
from query_pheno_data import query_data


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Query pheno properties")

    subparsers = parser.add_subparsers(title='subcommands',
        help='When no arguments given, subparsers list all respective queries')

    subparsers.add_parser('dbs',
        help='executes commands in relation to pheno databases.')
    i_parser = subparsers.add_parser('instruments',
        help='queries instruments  according to the given filters')
    m_parser = subparsers.add_parser('measures',
        help='queries measures according to the given filters')
    p_parser = subparsers.add_parser('people',
        help='queries people according to the given filters')

    i_parser.add_argument(
        '--phenodbs', type=str,
        default=None,
        help='pheno dbs (i.e. spark, agre, vip)'
    )

    m_parser.add_argument(
        '--phenodbs', type=str,
        default=None,
        help='pheno dbs (i.e. spark, agre, vip)'
    )
    m_parser.add_argument(
        '--instrumentIds', type=str,
        default=None,
        help='instrument IDs'
    )
    m_parser.add_argument(
        '--measureIds', type=str,
        default=None,
        help='measure IDs'
    )
    m_parser.add_argument(
        '--measureTypes', type=str,
        default=None,
        help='measure types. One of the following: continuous, ordinal, categorical, unknown'
    )

    p_parser.add_argument(
        '--phenodbs', type=str,
        default=None,
        help='pheno dbs (i.e. spark, agre, vip)'
    )
    p_parser.add_argument(
        '--measureIds', type=str,
        default=None,
        help='measure IDs'
    )
    p_parser.add_argument(
        '--instrumentIds', type=str,
        default=None,
        help='instrument IDs'
    )
    p_parser.add_argument(
        '--familyIds', type=str,
        default=None,
        help='family IDs'
    )
    p_parser.add_argument(
        '--familyIdsFile', type=str,
        default=None,
        help='file containing family IDs'
    )
    p_parser.add_argument(
        '--personIds', type=str,
        default=None,
        help='person IDs'
    )
    p_parser.add_argument(
        '--personIdsFile', type=str,
        default=None,
        help='file containing person IDs'
    )
    p_parser.add_argument(
        '--roles', type=str,
        default=None,
        help='roles in family (i.e. prb, sib, mom, dad)'
    )
    p_parser.add_argument(
        '--gender', type=str,
        default=None,
        help='person\'s gender. Can be M or F'
    )
    p_parser.add_argument(
        '--status', type=str,
        default=None,
        help='preson\'s status. Can be affected or unaffected'
    )
    p_parser.add_argument(
        '--measureTypes', type=str,
        default=None,
        help='measure types. One of the following: continuous, ordinal, categorical, unknown'
    )

    args = parser.parse_args(argv)

    args_dict = {a: getattr(args, a) for a in dir(args) if a[0] != '_'}

    return args_dict

if __name__ == "__main__":
    args_dict = parse_cli_arguments(sys.argv[1:])

    generator = query_data(args_dict)

    for l in generator:
        sys.stdout.write(join_line(l, '\t'))
