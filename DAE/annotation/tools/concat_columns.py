#!/usr/bin/env python

import argparse
from annotation.tools.utilities import AnnotatorBase, main, assign_values


def get_argument_parser():
    """
    ConcatColumnsAnnotator options::

        usage: concat_columns.py [-h] [-H] -c COLUMNS [-s SEP] [--label LABEL]
                         [infile] [outfile]

        Program to concatenate list of columns

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -H                    no header in the input file
          -c COLUMNS, --columns COLUMNS
                                comma separated list of columns to concatenate
          -s SEP, --sep SEP     separator
          --label LABEL         label for the generated column
    """
    desc = """Program to concatenate list of columns"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-H', help='no header in the input file',
        default=False,  action='store_true', dest='no_header')
    parser.add_argument(
        '-c', '--columns',
        help='comma separated list of columns to concatenate',
        required=True, action='store')
    parser.add_argument(
        '-s', '--sep', help='separator', default="",
        action='store')
    parser.add_argument(
        '--label', help='label for the generated column',
        default='concatenated', action='store')
    return parser


class ConcatColumnsAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(ConcatColumnsAnnotator, self).__init__(opts, header)

        self.columns_idx = [assign_values(col, header)
                            for col in opts.columns.split(',')]

        self._new_columns = ['result']
        self.header = self.header + [opts.label]

    @property
    def new_columns(self):
        return self._new_columns

    def line_annotations(self, line, new_columns):
        return [self.opts.sep.join([line[i - 1] for i in self.columns_idx])]


if __name__ == "__main__":
    main(get_argument_parser(), ConcatColumnsAnnotator)
