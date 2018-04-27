#!/usr/bin/env python
import sys, glob
import optparse
from collections import OrderedDict
from box import Box

from utilities import *
from annotate_score_base import ScoreAnnotator


def get_argument_parser():
    desc = """Program to annotate variants with multiple score files"""
    parser = optparse.OptionParser(description=desc)
    parser.add_option('-c', help='chromosome column number/name', action='store')
    parser.add_option('-p', help='position column number/name', action='store')
    parser.add_option('-x', help='location (chr:pos) column number/name', action='store')

    parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

    parser.add_option('-D', '--scores-directory',
        help='directory containing the scores - each score should have its own subdirectory '
              '(defaults to $GFD_DIR)',
        type='string', action='store')

    parser.add_option('--scores', help='comma separated list of scores to annotate with',
        type='string', action='store')
    parser.add_option('--scores-columns',
        help='comma separated list of columns to get the score; '
             'you should specify a score column for each score '
             '(defaults to score names)',
        type='string', action='store')
    parser.add_option('--labels',
        help='comma separated list of labels for the new columns in the output file '
             '(defaults to score names)',
        type='string', action='store')
    return parser


class MultipleScoresAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(MultipleScoresAnnotator, self).__init__(opts, header)
        self._init_score_directory()
        self._init_scores()
        if self.opts.labels is not None:
            self.header.extend(self.opts.labels.split(','))
        else:
            self.header.extend(self.scores)

    def _init_score_directory(self):
        self.scores_directory = self.opts.scores_directory
        if self.scores_directory is None:
            self.scores_directory = os.path.join(os.environ['GFD_DIR'])

    def _init_scores(self):
        if self.opts.scores is None:
            sys.stderr.write('--scores option is mandatory')
            sys.exit(-12)
        
        self.scores = self.opts.scores.split(',')
        if self.opts.scores_columns is None:
            scores_columns = self.scores
        else:
            scores_columns = self.opts.scores_columns.split(',')
        
        self.annotators = {}
        for (score, column) in list(zip(self.scores, scores_columns)):
            self.annotators[score] = ScoreAnnotator(
                self._opts_for_single_annotator(score, column),
                list(self.header), [], ['chrom', 'chromStart', 'chromEnd'])

    def _opts_for_single_annotator(self, score, column):
        opts = self.opts
        score_directory = self.scores_directory + '/' + score
        tabix_files = glob.glob(score_directory + '/*.tbi')
        if len(tabix_files) == 0:
            sys.stderr.write('could not find .tbi file for score {}'.format(score))
            sys.exit(-64)
        config = {
            'c': opts.c,
            'p': opts.p,
            'x': opts.x,
            'score_column': column,
            'direct': True,
            'scores_file': tabix_files[0].replace('.tbi', '')
        }
        return Box(config, default_box=True, default_box_attr=None)

    @property
    def new_columns(self):
        return self.scores

    def line_annotations(self, line, new_cols_order):
        result = []
        for col in new_cols_order:
            result.extend(self.annotators[col].line_annotations(line, [col]))
        return result


if __name__ == "__main__":
    main(get_argument_parser(), MultipleScoresAnnotator)
