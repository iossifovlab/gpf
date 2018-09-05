#!/usr/bin/env python
import argparse

from utilities import main
from annotate_score_base import ScoreAnnotator, conf_to_dict
from StringIO import StringIO


def get_argument_parser():
    """
    FrequencyAnnotator options::

        usage: annotateFreqTransm.py [-h] [-c C] [-p P] [-x X] [-v V] [-H]
                                 [-F SCORES_FILE]
                                 [--frequency FREQUENCY] [--direct]
                                 [--label LABEL]
                                 [infile] [outfile]

        Program to annotate variants with frequencies

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -c C                  chromosome column number/name
          -p P                  position column number/name
          -x X                  location (chr:pos) column number/name
          -v V                  variant column number/name
          -H                    no header in the input file
          -F SCORES_FILE, --scores-file SCORES_FILE
                                file containing the scores
          --frequency FREQUENCY comma separated list of frequencies to annotate the output file with
          --direct              the score files is tabix indexed
          --labels LABEL        label of the new column; defaults to the name of the
                                score column
          --default-value DEFAULT_VALUE
                                default value if score for variant is not found
    """
    desc = """Program to annotate variants with frequencies"""
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument('-v', help='variant column number/name', default='variant', action='store')
    parser.add_argument('-H', help='no header in the input file', action='store_true', dest='no_header')
    parser.add_argument('-F', '--scores-file', help='file containing the scores',
                        type=str, action='store')
    parser.add_argument('--frequency', help='comma separated list of frequencies to annotate with (defaults to all.altFreq)',
                        action='store', default='all.altFreq')
    parser.add_argument('--direct', help='the score files is tabix indexed', action='store_true')
    parser.add_argument('--labels', help='labels of the new column; defaults to the name of the score column',
                        type=str, action='store')
    parser.add_argument('--default-value', help='default value if score for variant is not found',
                        default='', type=str, action='store')
    return parser


FREQ_SCORE_CONFIG = '''
[general]
header=chr,position,variant,familyData,all_nParCalled,all_prcntParCalled,all_nAltAlls,all_altFreq,effectType,effectGene,effectDetails,segDups,HW,SSC-freq,EVS-freq,E65-freq
noScoreValue=
[columns]
chr=chr
pos_begin=position
score=all_nParCalled,all_prcntParCalled,all_nAltAlls,all_altFreq
search=variant
'''


class FrequencyAnnotator(ScoreAnnotator):

    def __init__(self, opts, header=None):
        opts.scores_config_file = conf_to_dict(StringIO(FREQ_SCORE_CONFIG))
        if opts.default_value != '' and opts.default_value is not None:
            opts.scores_config_file['noScoreValue'] = opts.default_value
        opts.search_columns = opts.v
        self.freqcols = opts.frequency.split(',')
        super(FrequencyAnnotator, self).__init__(opts, header)

    @property
    def new_columns(self):
        return self.freqcols


if __name__ == "__main__":
    main(get_argument_parser(), FrequencyAnnotator)
