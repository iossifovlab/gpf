#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
import sys
import argparse
from DAE import vDB
from query_variants import join_line


STUDY_HEADER = ['study', 'name', 'has denovo', 'has transmitted',
                'description']
STUDY_GROUP_HEADER = ['study group', 'name', 'description', 'study names']


def str_arr(arr):
    return [str(el) for el in arr]


def form_studies():
    yield STUDY_HEADER
    for study_name in vDB.get_study_names():
        st = vDB.get_study(study_name)
        description = st.description.replace('\n', ' ')
        yield str_arr([study_name, st.name, st.has_denovo,
                       st.has_transmitted, description])


def form_study_groups():
    yield STUDY_GROUP_HEADER
    for study_group_name in vDB.get_study_group_names():
        group = vDB.get_study_group(study_group_name)
        yield str_arr([study_group_name, group.name, group.description,
                       ', '.join(group.studyNames)])


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Query studies and study groups')

    parser.add_argument(
        '--studies-only',
        action='store_true',
        help='queries only studies')

    parser.add_argument(
        '--groups-only',
        action='store_true',
        help='queries only study groups')

    parser_args = parser.parse_args(argv)
    return parser_args


if __name__ == '__main__':
    args = parse_cli_arguments()

    if not args.groups_only:
        study_gen = form_studies()
        for line in study_gen:
            sys.stdout.write(join_line(line))

    sys.stdout.write('\n')

    if not args.studies_only:
        study_groups_gen = form_study_groups()
        for line in study_groups_gen:
            sys.stdout.write(join_line(line))
