#!/usr/bin/env python

import sys
import argparse
from utilities import *

def get_argument_parser():
    """
    RelabelChromosomeAnnotator options::

        usage: relabel_chromosome.py [-h] [-c C] [-H] [--new-c NEW_C]
                                 [infile] [outfile]

        Program to relabel chromosome with or without 'chr' prefix

        positional arguments:
          infile         path to input file; defaults to stdin
          outfile        path to output file; defaults to stdout

        optional arguments:
          -h, --help     show this help message and exit
          -c C           chromosome column number/name
          -H             no header in the input file
          --new-c NEW_C  name for the generated chromosome column

    """
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
