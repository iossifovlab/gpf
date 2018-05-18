#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import unicode_literals
import sys
import argparse
from .utilities import *

def get_argument_parser():
    desc = """Program to relabel chromosome with or without 'chr' prefix"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-H', help='no header in the input file', default=False,  action='store_true', dest='no_header')
    parser.add_argument('--new-c', help='name for the generated chromosome column', default='relabledChr', action='store')
    return parser


class RelabelChromosomeAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(RelabelChromosomeAnnotator, self).__init__(opts, header)

        self.chrCol = assign_values(opts.c, header)

        self._new_columns = ['new_c']
        self.header = self.header + [opts.new_c]

    @property
    def new_columns(self):
        return self._new_columns

    def line_annotations(self, line, new_columns):
        chromosome = line[self.chrCol - 1]
        if not chromosome:
            return [chromosome]
        if 'chr' in chromosome:
            return [chromosome.replace('chr', '')]
        else:
            return ['chr' + chromosome]


if __name__ == "__main__":
    main(get_argument_parser(), RelabelChromosomeAnnotator)
