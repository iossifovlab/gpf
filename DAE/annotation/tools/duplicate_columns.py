#!/usr/bin/env python

import argparse
from utilities import *


def get_argument_parser():
    """
    DuplicateColumnsAnnotator options::

        usage: duplicate_columns.py [-h] [-H] -c COLUMNS -l LABELS [infile] [outfile]

        Program to duplicate list of columns

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -H                    no header in the input file
          -c COLUMNS, --columns COLUMNS
                                comma separated list of columns to duplicate
          -l LABELS, --labels LABELS
                                comma separated list of labels for the new columns
    """
    desc = """Program to duplicate list of columns"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-H', help='no header in the input file',
                        default=False, action='store_true',
                        dest='no_header')
    parser.add_argument('-c', '--columns',
                        help='comma separated list of columns to duplicate',
                        required=True, action='store')
    parser.add_argument('-l', '--labels',
                        help='comma separated list of labels for the new columns',
                        required=True, action='store')
    return parser


class DuplicateColumnsAnnotator(AnnotatorBase):
    """
    With `DuplicateColumnsAnnotator` you can duplicate columns.
    """

    def __init__(self, opts, header=None):
        super(DuplicateColumnsAnnotator, self).__init__(opts, header)

        self.columns_idx = {col: assign_values(col, header)
                            for col in opts.columns.split(',')}

        if opts.labels is None:
            opts.labels = opts.columns

        self._new_columns = opts.columns.split(',')

        if self.header:
            self.header = self.header + opts.labels.split(',')

    @property
    def new_columns(self):
        return self._new_columns

    def line_annotations(self, line, new_columns):
        return [line[self.columns_idx[col] - 1] for col in new_columns]


if __name__ == '__main__':
    main(get_argument_parser(), DuplicateColumnsAnnotator)
