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
    parser.add_argument('-v', help='variant column number/name', default='variant', action='store')
    parser.add_argument('-H', help='no header in the input file', action='store_true', dest='no_header')
    parser.add_argument('-F', '--scores-file', help='file containing the scores',
                        type=str, action='store')
    parser.add_argument('--scores-config-file', help='file containing the config for the scores file',
                        action='store')
    parser.add_argument('--direct', help='the score files is tabix indexed', action='store_true')
    parser.add_argument('--labels', help='labels of the new column; defaults to the name of the score column',
                        type=str, action='store')
    return parser


class FrequencyAnnotator(ScoreAnnotator):

    def __init__(self, opts, header=None):
        super(FrequencyAnnotator, self).__init__(opts, header, [opts.v])


if __name__ == "__main__":
    main(get_argument_parser(), FrequencyAnnotator)
