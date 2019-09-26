#!/usr/bin/env python
import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.family import FamiliesBase


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='simple import of new study data',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        'family_filename', type=str,
        metavar='<family filename>',
        help='families file in simple families format'
    )
    parser.add_argument(
        '--id', type=str,
        metavar='<study ID>',
        dest="id",
        help='Unique study ID to use. '
        'If not specified the basename of the family file is used '
        'for study ID'
    )

    parser.add_argument(
        '-o', '--out', type=str, default=None,
        dest='output', metavar='<output filename>',
        help='output filename. If not specified the output filename'
        'is constructed from <study id>.ped'
    )
    parser_args = parser.parse_args(argv)
    return parser_args


def main(argv):
    args = parse_cli_arguments(argv[1:])
    if args.id is not None:
        study_id = args.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(args.family_filename))

    if args.output is None:
        output = "{study_id}.ped".format(study_id=study_id)
    else:
        output = argv.output

    gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config

    fam_df = FamiliesBase.load_simple_family_file(args.family_filename)
    FamiliesBase.save_pedigree(fam_df, output)

if __name__ == "__main__":
    main(sys.argv)
