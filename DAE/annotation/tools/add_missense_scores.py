#!/usr/bin/env python
import argparse
import os
from box import Box

from .utilities import AnnotatorBase, assign_values, main
from .annotate_score_base import ScoreAnnotator, conf_to_dict


def get_argument_parser():
    """
    `MissenseScoresAnnotator` options::

        usage: add_missense_scores.py [-h]
                            [-c C] [-p P] [-x X] [-r R] [-a A] [-H]
                            [--dbnsfp DBNSFP] [--columns COLUMNS] [--direct]
                            [--reference-genome {hg19,hg38}]
                            [infile] [outfile]

        Add missense scores from dbSNFP

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -c C                  chromosome column number/name
          -p P                  position column number/name
          -x X                  location (chr:pos) column number/name
          -r R                  reference column number/name
          -a A                  alternative column number/name
          -H                    no header in the input file
          --dbnsfp DBNSFP       path to dbNSFP
          --config CONFIG       path to .conf file for score file, defaults to
                                score name
          --columns COLUMNS     score columns to include in the output file
          --direct              read score files using tabix index (default:
                                read score files iteratively)
          --labels              comma separated list of the new header entries,
                                defaults to added columns' names
    """

    parser = argparse.ArgumentParser(
        description='Add missense scores from dbSNFP')
    parser.add_argument(
        '-c', help='chromosome column number/name', action='store')
    parser.add_argument(
        '-p', help='position column number/name', action='store')
    parser.add_argument(
        '-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument(
        '-r', help='reference column number/name', action='store')
    parser.add_argument(
        '-a', help='alternative column number/name', action='store')
    parser.add_argument(
        '-H', help='no header in the input file',
        default=False,  action='store_true', dest='no_header')
    parser.add_argument(
        '--dbnsfp', help='path to dbNSFP', action='store')
    parser.add_argument(
        '--config', help='path to config', action='store')
    parser.add_argument(
        '--columns',
        help='comma separated list of score columns to annotate with',
        action='store')
    parser.add_argument(
        '--direct',
        help='read score files using tabix index '
        '(default: read score files iteratively)',
        default=False, action='store_true')
    parser.add_argument(
        '--labels', help='comma separated list of the new labels '
        'of the added columns, defaults to column names', action='store')
    return parser


class MissenseScoresAnnotator(AnnotatorBase):

    CHROMOSOMES = [str(i) for i in range(1, 23)] + ['X', 'Y']

    def __init__(self, opts, header=None):
        self.opts = opts
        self.header = header
        if self.opts.columns is not None:
            self.opts.columns = self.opts.columns.split(',')
            self.header.extend(self.opts.columns)
        if opts.dbnsfp is None:
            opts.dbnsfp = os.path.join(os.environ['dbNSFP_PATH'])
        self.path = opts.dbnsfp
        self.annotators = {}
        self._init_cols()

    def _init_cols(self):
        if self.opts.x is None and self.opts.c is None:
            self.opts.x = 'location'
        if self.opts.r is None:
            self.opts.r = 'ref'
        if self.opts.a is None:
            self.opts.a = 'alt'
        self.loc_idx = assign_values(self.opts.x, self.header)
        self.chr_idx = assign_values(self.opts.c, self.header)
        self.pos_idx = assign_values(self.opts.p, self.header)

    def _annotator_for(self, chr, scores):
        if chr not in self.annotators:
            if chr not in self.CHROMOSOMES:
                return None

            if self.opts.config is None:
                score_conf = self.path.format(chr) + '.conf'
            else:
                score_conf = conf_to_dict(self.opts.config)
            config = {
                'c': self.opts.c,
                'p': self.opts.p,
                'x': self.opts.x,
                'search_columns': ','.join([self.opts.r, self.opts.a]),
                'direct': self.opts.direct,
                'scores_file': self.path.format(chr),
                'scores_config_file': score_conf,
                'labels': self.opts.labels,
            }
            score_annotator_opts = Box(
                config, default_box=True, default_box_attr=None)

            self.annotators[chr] = ScoreAnnotator(
                    score_annotator_opts,
                    header=list(self.header))
        return self.annotators[chr]

    def _get_chr(self, line):
        if self.loc_idx is not None:
            chr = line[self.loc_idx-1].split(':')[0]
        elif self.chr_idx is not None:
            chr = line[self.chr_idx-1]
        return chr.replace('chr', '')

    @property
    def new_columns(self):
        return self.opts.columns

    def line_annotations(self, line, new_cols_order):
        annotator = self._annotator_for(self._get_chr(line), new_cols_order)
        if annotator is not None:
            return annotator.line_annotations(line, new_cols_order)
        else:
            return ['' for value in new_cols_order]


if __name__ == "__main__":
    main(get_argument_parser(), MissenseScoresAnnotator)
