#!/usr/bin/env python

from __future__ import print_function
import sys
import argparse
import random
import pandas as pd


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Convert denovo data to DAE")

    parser.add_argument(
        'variantsFile', type=str,
        help='VCF format variant file. Available formats include'
             ' .tsv, .csv, .xlsx'
    )
    parser.add_argument(
        '--skiprows', type=int, default=0,
        metavar='NumberOfRows',
        help='number of rows to be skipped from variants file.'
             ' Applied only for xlsx files'
    )
    parser.add_argument(
        '-f', '--file', type=str, default=None,
        dest='outputFile', metavar='outputFileName',
        help='output filepath'
    )
    parser.add_argument(
        '-i', '--sampleIdColumn',
        type=str, default='sampleId',
        dest='sampleId', metavar='sampleIdColumn',
        help='column name for sampleId. Default is \'sampleId\''
    )
    parser.add_argument(
        '-s', '--statusColumn',
        type=str, default='status',
        dest='status', metavar='statusColumn',
        help='column name for status. Default is \'status\''
    )
    parser.add_argument(
        '-g', '--genderColumn',
        type=str, default='gender',
        dest='gender', metavar='genderColumn',
        help='column name for gender. Default is \'gender\''
    )

    args = parser.parse_args(argv)
    return {a: getattr(args, a) for a in dir(args) if a[0] != '_'}


def import_file(filepath, skiprows=0):
    extension = filepath.split('.').pop()
    try:
        if extension == 'tsv' or extension == 'ped':
            return pd.read_table(filepath, sep='\t')
        elif extension == 'csv':
            return pd.read_csv(filepath)
        elif extension == 'xlsx':
            return pd.read_excel(filepath, skiprows=skiprows)
        else:
            raise IOError
    except IOError:
        print('ERROR: Incorrect filepath: {}'.format(filepath),
              file=sys.stderr)
        sys.exit(1)


def prepare_args(args):
    if not args['outputFile']:
        args['outputFile'] = '.'.join(
            args['variantsFile'].split('.')[:-1]) + '-families.tsv'


def randomize_gender(l):
    return [random.choice(['M', 'F']) for i in range(l)]


def randomize_status(l):
    return [random.choice([1, 2]) for i in range(l)]


def handle_column(col, variants, rand_func, arg):
    if col.lower() == 'none':
        return rand_func(arg)
    try:
        return variants[col]
    except KeyError:
        print('ERROR: {} column does not exist. Assigning random values...'
              .format(col), file=sys.stderr)
        return rand_func(arg)


def denovo2ped(args):
    variants = import_file(args['variantsFile'], args['skiprows'])

    families = pd.DataFrame(variants, columns=[args['sampleId']]) \
        .rename(columns={args['sampleId']: 'personId'})
    families = families.drop_duplicates()

    families['familyId'] = families['personId']
    families['momId'] = '0'
    families['dadId'] = '0'
    families['role'] = 'prb'
    families['gender'] = handle_column(args['gender'], variants,
                                       randomize_gender, len(families))
    families['status'] = handle_column(args['status'], variants,
                                       randomize_status, len(families))

    families.to_csv(args['outputFile'], sep='\t', index=False)
    print('Exported to filepath: {}'.format(args['outputFile']),
          file=sys.stderr)


if __name__ == '__main__':
    args_dict = parse_cli_arguments(sys.argv[1:])
    prepare_args(args_dict)
    denovo2ped(args_dict)
