#!/usr/bin/env python
import sys
import glob
import argparse
import os.path
from os import listdir
from box import Box

from utilities import AnnotatorBase, main
from annotate_score_base import ScoreAnnotator


def get_argument_parser():
    """
    MultipleScoresAnnotator options::

        usage: annotate_with_multiple_scores.py [-h] [-c C] [-p P] [-x X] [-H]
                                        [-D SCORES_DIRECTORY] [--direct]
                                        [--scores SCORES] [--labels LABELS]
                                        [infile] [outfile]

        Program to annotate variants with multiple score files

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -c C                  chromosome column number/name
          -p P                  position column number/name
          -x X                  location (chr:pos) column number/name
          -H                    no header in the input file
          -D SCORES_DIRECTORY, --scores-directory SCORES_DIRECTORY
                                directory containing the scores - each score should
                                have its own subdirectory (defaults to $GFD_DIR)
          --direct              read score files using tabix index (default: read
                                score files iteratively)
          --scores SCORES       comma separated list of scores to annotate with
          --labels LABELS       comma separated list of labels for the new columns in
                                the output file (defaults to score names)
    """
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
    parser.add_argument('--labels',
                        help='comma separated list of labels for the new columns in the output file '
                        '(defaults to score names)',
                        action='store')
    return parser


def get_dirs(path):
    path = os.path.abspath(path)
    return [path + '/' + dir_ for dir_ in listdir(path) if len(dir_.split('.')) == 1]


def get_files(path):
    path = os.path.abspath(path)
    return [path + '/' + dir_ for dir_ in listdir(path) if len(dir_.split('.')) > 1]


def get_score(path):
    conf = [f.split('.') for f in get_files(path) if 'conf' in f.split('.')]
    if not conf:
        sys.stderr.write('Could not find score config file in ' + path + '\n')
        sys.exit(-64)
    else:
        conf = conf[0]
        conf.remove('conf')
        return '.'.join(conf)


def assert_tabix(score):
    score_path = os.path.dirname(score)
    tabix_files = glob.glob(score_path + '/*.tbi')
    if len(tabix_files) == 0:
        sys.stderr.write('could not find .tbi file for score {}'.format(score))
        sys.exit(-64)
    return True


class MultipleScoresAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(MultipleScoresAnnotator, self).__init__(opts, header)
        self._init_score_directory()
        self.annotators = {}
        if opts.scores is not None:
            self.scores = opts.scores.split(',')
        else:
            self.scores = None
        if self.opts.labels is not None:
            self.header.extend(self.opts.labels.split(','))
        elif self.scores is not None:
            self.header.extend(self.scores)

    def _init_score_directory(self):
        self.scores_directory = self.opts.scores_directory
        if self.scores_directory is None:
            self.scores_directory = os.path.join(os.environ['GFD_DIR'])

    def _annotator_for(self, score):
        if score not in self.annotators:
            score_dir = '{dir}/{score}'.format(dir=self.scores_directory, score=score) 
            score_file = None
            for file in get_files(score_dir):
                if file[-3:] == '.gz':
                    score_file = file
                    break
            if score_file is None:
                sys.stderr.write('could not find score file for score {}'.format(score))
            if self.opts.direct:
                assert_tabix(score_file)

            config = {
                'c': self.opts.c,
                'p': self.opts.p,
                'x': self.opts.x,
                'scores_file': score_file,
                'direct': self.opts.direct,
                'labels': self.opts.labels,
            }

            score_annotator_opts = Box(config, default_box=True, default_box_attr=None)
            self.annotators[score] = ScoreAnnotator(score_annotator_opts,
                                                    list(self.header))

        return self.annotators[score]

    @property
    def new_columns(self):
        if self.opts.scores is None or self.opts.scores == '':
            sys.stderr.write('--scores option is mandatory!\n')
            sys.exit(-12)
        return self.scores

    def line_annotations(self, line, new_cols_order):
        result = []
        for col in new_cols_order:
            annotator = self._annotator_for(col)
            annotations = annotator.line_annotations(line, annotator.new_columns)
            if len(annotations) > 1:
                annotations = ['|'.join(annotations)]
            result.extend(annotations)
        return result


if __name__ == "__main__":
    main(get_argument_parser(), MultipleScoresAnnotator)
