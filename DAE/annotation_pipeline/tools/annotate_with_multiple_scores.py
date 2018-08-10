#!/usr/bin/env python
import sys
import glob
import argparse
import os.path
from box import Box

from utilities import AnnotatorBase, main
from annotate_score_base import ScoreAnnotator


def get_argument_parser():
    desc = """Program to annotate variants with multiple score files"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')

    parser.add_argument('-H',
                        help='no header in the input file', default=False,
                        action='store_true', dest='no_header')
    parser.add_argument('-D', '--scores-directory',
                        help='directory containing the scores - each score should have its own subdirectory '
                        '(defaults to $GFD_DIR)',
                        action='store')
    parser.add_argument('--direct',
                        help='read score files using tabix index '
                        '(default: read score files iteratively)',
                        default=False, action='store_true')
    parser.add_argument('--scores',
                        help='comma separated list of scores to annotate with',
                        action='store')
    parser.add_argument('--scores-configs',
                        help='ordered, comma separated list of score config files '
                        '(defaults to score names with a .conf suffix)',
                        action='store')
    parser.add_argument('--labels',
                        help='comma separated list of labels for the new columns in the output file '
                        '(defaults to score names)',
                        action='store')
    parser.add_argument('--explicit',
                        help='when passed, interprets the --scores option as a list of real paths',
                        action='store_true')
    return parser


class MultipleScoresAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(MultipleScoresAnnotator, self).__init__(opts, header)
        self._init_score_directory()
        self._init_scores()
        if self.opts.labels is not None:
            self.header.extend(self.opts.labels.split(','))
        elif self.scores is not None:
            self.header.extend(self.scores)

    def _init_score_directory(self):
        self.scores_directory = self.opts.scores_directory
        if self.scores_directory is None:
            self.scores_directory = os.path.join(os.environ['GFD_DIR'])

    def _init_scores(self):
        self.annotators = {}
        if self.opts.scores is not None:
            self.scores = self.opts.scores.split(',')
            self.scores_configs = self.opts.scores_configs.split(',')
        else:
            self.scores = None

    def _annotator_for(self, score, score_config):
        if score not in self.annotators:
            opts = self.opts
            score_directory = self.scores_directory
            if not opts.explicit:
                score_directory += '/' + score

            if not os.path.isdir(score_directory):
                sys.stderr.write('directory for "{}" not found, please provide only valid scores'.format(score))
                sys.exit(-78)

            if opts.direct:
                tabix_files = glob.glob(score_directory + '/*.tbi')
                if len(tabix_files) == 0:
                    sys.stderr.write('could not find .tbi file for score {}'.format(score))
                    sys.exit(-64)

            config = {
                'c': opts.c,
                'p': opts.p,
                'x': opts.x,
                'scores_file': score,
                'scores_config_file': score_config,
                'direct': opts.direct,
                'labels': opts.labels
            }

            score_annotator_opts = Box(config, default_box=True, default_box_attr=None)
            self.annotators[score] = ScoreAnnotator(score_annotator_opts,
                                                    list(self.header), [])

        return self.annotators[score]

    @property
    def new_columns(self):
        if self.scores is None:
            sys.stderr.write('--scores option is mandatory')
            sys.exit(-12)
        return self.scores

    def line_annotations(self, line, new_cols_order):
        result = []
        for score in self.scores:
            if self.scores.index(score) < len(self.scores_configs):
                score_config = self.scores_configs[self.scores.index(score)]
            else:
                score_config = None
            result.extend(self._annotator_for(score, score_config).line_annotations(line, [score]))
        return result


if __name__ == "__main__":
    main(get_argument_parser(), MultipleScoresAnnotator)
