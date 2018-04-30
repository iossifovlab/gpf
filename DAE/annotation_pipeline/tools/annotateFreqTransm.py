#!/usr/bin/env python
import optparse

from utilities import main
from annotate_score_base import ScoreAnnotator


def get_argument_parser():
    desc = """Program to annotate variants with frequencies"""
    parser = optparse.OptionParser(description=desc)
    parser.add_option('-c', help='chromosome column number/name', action='store')
    parser.add_option('-p', help='position column number/name', action='store')
    parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_option('-v', help='variant column number/name', action='store')

    parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

    parser.add_option('-F', '--scores-file', help='file containing the scores', type='string', action='store')
    parser.add_option('--direct', help='the score files is tabix indexed', default=False, action='store_true')

    parser.add_option('--score-column', help='column in score file that contains the score (default: all.altFreq)', default='all.altFreq', type='string', action='store')
    parser.add_option('--label', help='label of the new column; defaults to the name of the score column', type='string', action='store')

    return parser


class FrequencyAnnotator(ScoreAnnotator):

    def __init__(self, opts, header=None):
        if opts.v is None:
            opts.v = 'variant'
        super(FrequencyAnnotator, self).__init__(opts, header, [opts.v],
            ['chr', 'position', 'position', 'variant'])

if __name__ == "__main__":
    main(get_argument_parser(), FrequencyAnnotator)
