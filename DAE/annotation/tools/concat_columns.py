#!/usr/bin/env python

import sys
import argparse
from utilities import *

def get_argument_parser():
    desc = """Program to concatenate list of columns"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-H', help='no header in the input file',
        default=False,  action='store_true', dest='no_header')
    parser.add_argument('-c', '--columns',
        help='comma separated list of columns to concatenate',
        required=True, action='store')
    parser.add_argument('-s', '--sep', help='separator', default="",
        action='store')
    parser.add_argument('--label', help='label for the generated column',
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
