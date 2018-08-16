#!/usr/bin/env python

from __future__ import print_function
from DAE import vDB
import sys, argparse

def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Compares studies with denovo db')

    parser.add_argument(
        'study', type=str,
        help='study name to be compared with denovo db'
    )
    parser.add_argument(
        'denovo-study', type=str,
        help='study name from denovo db'
    )

    args = parser.parse_args(argv)
    return {a: getattr(args, a) for a in dir(args) if a[0] != '_'}

def fill_data(d_all, n_all, study_name, denovo_study_name):
    new_study = vDB.get_study(study_name)
    denovo_study = vDB.get_study('denovo_db')

    for v in denovo_study.get_denovo_variants():
        if (v.atts['StudyName'] == denovo_study_name or v.atts['StudyName'] == 'Yuen2016'):
            d_all.append(v.atts['loc'] + '|' + v.atts['var'] + '|' + v.atts['SampleID'])

    for v in new_study.get_denovo_variants():
        if ',' in v.atts['sampleIds']:
            for id in v.atts['sampleIds'].split(', '):
                n_all.append(v.atts['location'] + '|' + v.atts['variant'] + '|' + id)
        else:
            n_all.append(v.atts['location'] + '|' + v.atts['variant'] + '|' + v.atts['sampleIds'])

def remove_dups(arr):
    seen = set()
    uniq = []
    for x in arr:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq

def common_data(arr1, arr2):
    common = []
    for v in arr1:
        if v in arr2:
            common.append(v)
    return common

def remove_data(dest, to_remove):
    return [v for v in dest if v not in to_remove]

def status(d_all, n_all, study_name):
    print('denovo: {}, {}: {}'.format(len(d_all), study_name, len(n_all)), file=sys.stdout)

def compare(args):
    study_name = args['study']
    d_all, n_all = [], []

    print('...Retrieving variants...', file=sys.stdout)
    fill_data(d_all, n_all, study_name, args['denovo-study'])
    status(d_all, n_all, study_name)

    print('...Removing duplicates...', file=sys.stdout)
    d_all = remove_dups(d_all)
    n_all = remove_dups(n_all)
    status(d_all, n_all, study_name)

    print('...Finding common variants...', file=sys.stdout)
    common_all = common_data(n_all, d_all)
    print('common variants: {}'.format(len(common_all)), file=sys.stdout)

    print('...Finding unmatching data...', file=sys.stdout)
    d_all = remove_data(d_all, common_all)
    n_all = remove_data(n_all, common_all)
    status(d_all, n_all, study_name)

    if not n_all: return None

    print('\nList of unmatching {} {} variants:'.
            format(len(n_all), study_name), file=sys.stdout)
    for v in n_all:
        loc,var,ids = v.split('|')
        print('SampleId: {}, Location: {}, Variant: {}'
            .format(ids,loc,var), file=sys.stdout)
    return n_all, d_all

if __name__ == '__main__':
    args_dict = parse_cli_arguments(sys.argv[1:])
    compare(args_dict)
