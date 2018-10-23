#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import unicode_literals

from .annotator_base import AnnotatorBase


# def get_argument_parser():
#     """
#     RelabelChromosomeAnnotator options::

#         usage: relabel_chromosome.py [-h] [-c C] [-H] [--new-c NEW_C]
#                                  [infile] [outfile]

#         Program to relabel chromosome with or without 'chr' prefix

#         positional arguments:
#           infile         path to input file; defaults to stdin
#           outfile        path to output file; defaults to stdout

#         optional arguments:
#           -h, --help     show this help message and exit
#           -c C           chromosome column number/name
#           -H             no header in the input file
#           --new-c NEW_C  name for the generated chromosome column

#     """
#     desc = """Program to relabel chromosome with or without 'chr' prefix"""
#     parser = argparse.ArgumentParser(description=desc)
#     parser.add_argument(
#         '-c', help='chromosome column number/name', action='store')
#     parser.add_argument(
#         '-H', help='no header in the input file',
#         default=False,  action='store_true', dest='no_header')
#     parser.add_argument(
#         '--new-c', help='name for the generated chromosome column',
#         default='relabledChr', action='store')
#     return parser


class RelabelChromosomeAnnotator(AnnotatorBase):

    def __init__(self, config):
        super(RelabelChromosomeAnnotator, self).__init__(config)

        assert self.config.options.c is not None
        assert self.config.options.new_c is not None
        self.chrom_column = self.config.options.c
        self.chrom_new_column = self.config.options.new_c

    def line_annotation(self, annotation_line, variant=None):
        value = annotation_line.columns.get(self.chrom_column, None)
        if not value:
            value = ''
        if 'chr' in value:
            value = value.replace('chr', '')
        else:
            value = 'chr' + value
        annotation_line.columns[self.chrom_new_column] = value


# if __name__ == "__main__":
#     main(get_argument_parser(), RelabelChromosomeAnnotator)
