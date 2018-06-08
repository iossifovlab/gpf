#!/usr/bin/env python
import argparse

from utilities import main
from annotate_score_base import ScoreAnnotator


def get_argument_parser():
    desc = """Program to annotate variants with frequencies"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument('-v', help='variant column number/name', action='store')

    parser.add_argument('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

    parser.add_argument('-F', '--scores-file', help='file containing the scores', type=str, action='store')
    parser.add_argument('--direct', help='the score files is tabix indexed', default=False, action='store_true')

    parser.add_argument('--score-column', help='column in score file that contains the score (default: all.altFreq)', type=str, action='store')
    parser.add_argument('--default-value', help='default value if score for variant is not found', default='', type=str, action='store')
    parser.add_argument('--label', help='label of the new column; defaults to the name of the score column', type=str, action='store')

    return parser


class FrequencyAnnotator(ScoreAnnotator):

    def __init__(self, opts, header=None):
        if opts.v is None:
            opts.v = 'variant'

        if opts.score_column is None:
            opts.scores_columns = 'all.altFreq'
        else:
            opts.scores_columns = opts.score_column

        if opts.default_value is None:
            opts.default_values = ''
        else:
            opts.default_values = opts.default_value

        opts.labels = opts.label
        super(FrequencyAnnotator, self).__init__(opts, header, [opts.v],
            None, ['chr', 'position', 'position', 'variant'])

if __name__ == "__main__":
    main(get_argument_parser(), FrequencyAnnotator)
